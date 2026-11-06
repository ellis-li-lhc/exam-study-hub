import Foundation
import Vision
import ImageIO
for path in CommandLine.arguments.dropFirst() {
 let url=URL(fileURLWithPath:path)
 let request=VNRecognizeTextRequest()
 request.recognitionLevel = .accurate
 request.recognitionLanguages = ["zh-Hans", "en-US"]
 request.usesLanguageCorrection = false
 try VNImageRequestHandler(url:url).perform([request])
 let result=(request.results ?? []).compactMap { item -> [String:Any]? in
  guard let candidate=item.topCandidates(1).first else { return nil }
  let b=item.boundingBox
  return ["text":candidate.string,"confidence":candidate.confidence,"x":b.minX,"y":b.minY,"w":b.width,"h":b.height]
 }
 let data=try JSONSerialization.data(withJSONObject:result,options:[.sortedKeys])
 let output=url.deletingPathExtension().appendingPathExtension("ocr.json")
 try data.write(to:output)
 print(url.lastPathComponent,result.count)
}
