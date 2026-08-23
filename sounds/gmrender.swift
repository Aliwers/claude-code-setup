// Оффлайн-рендер коротких фраз через штатный GM-сэмплер macOS.
//
//   gmrender <program> <out.wav> <pitch:start:dur:velocity> ...
//
// program — номер инструмента General MIDI (0 = рояль, 46 = арфа, ...).
// Банк сэмплов берётся из CoreAudio, поэтому звучит как инструмент,
// а не как сложенные синусоиды.
import AVFoundation

let args = CommandLine.arguments
guard args.count >= 4, let program = UInt8(args[1]) else {
    FileHandle.standardError.write(Data("usage: gmrender <program> <out.wav> <pitch:start:dur:vel> ...\n".utf8))
    exit(2)
}
let outURL = URL(fileURLWithPath: args[2])

struct Note { let pitch: UInt8; let start: Double; let duration: Double; let velocity: UInt8 }
let notes: [Note] = args.dropFirst(3).map { spec in
    let f = spec.split(separator: ":").map(String.init)
    return Note(pitch: UInt8(f[0]) ?? 60, start: Double(f[1]) ?? 0,
                duration: Double(f[2]) ?? 0.5, velocity: UInt8(f.count > 3 ? f[3] : "70") ?? 70)
}

let sampleRate = 44100.0
let release = 1.6   // хвост, чтобы послезвучие не обрывалось
let total = (notes.map { $0.start + $0.duration }.max() ?? 1.0) + release

let engine = AVAudioEngine()
let sampler = AVAudioUnitSampler()
engine.attach(sampler)
engine.connect(sampler, to: engine.mainMixerNode, format: nil)

let format = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 2)!
try engine.enableManualRenderingMode(.offline, format: format, maximumFrameCount: 4096)
try engine.start()
try sampler.loadSoundBankInstrument(
    at: URL(fileURLWithPath: "/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls"),
    program: program, bankMSB: UInt8(kAUSampler_DefaultMelodicBankMSB), bankLSB: 0)

// AVAudioFile дописывает заголовок WAV только при освобождении,
// а глобалы в top-level коде не освобождаются при exit — держим опционально.
var file: AVAudioFile? = try AVAudioFile(forWriting: outURL, settings: [
    AVFormatIDKey: kAudioFormatLinearPCM,
    AVSampleRateKey: sampleRate,
    AVNumberOfChannelsKey: 2,
    AVLinearPCMBitDepthKey: 16,
    AVLinearPCMIsFloatKey: false
])
let buffer = AVAudioPCMBuffer(pcmFormat: engine.manualRenderingFormat,
                              frameCapacity: engine.manualRenderingMaximumFrameCount)!

// События нот выставляются на границах блоков рендера — сэмплер живёт
// в реальном времени, а offline-режим двигает его время нашими вызовами.
var events = notes.flatMap { note in
    [(frame: AVAudioFramePosition(note.start * sampleRate), pitch: note.pitch, on: true, vel: note.velocity),
     (frame: AVAudioFramePosition((note.start + note.duration) * sampleRate), pitch: note.pitch, on: false, vel: note.velocity)]
}.sorted { $0.frame < $1.frame }

var rendered: AVAudioFramePosition = 0
let target = AVAudioFramePosition(total * sampleRate)
while rendered < target {
    while let next = events.first, next.frame <= rendered {
        if next.on { sampler.startNote(next.pitch, withVelocity: next.vel, onChannel: 0) }
        else { sampler.stopNote(next.pitch, onChannel: 0) }
        events.removeFirst()
    }
    let chunk = AVAudioFrameCount(min(AVAudioFramePosition(buffer.frameCapacity), target - rendered))
    guard try engine.renderOffline(chunk, to: buffer) == .success else { exit(1) }
    try file?.write(from: buffer)
    rendered += AVAudioFramePosition(chunk)
}
engine.stop()
file = nil   // закрывает файл и дописывает заголовок
