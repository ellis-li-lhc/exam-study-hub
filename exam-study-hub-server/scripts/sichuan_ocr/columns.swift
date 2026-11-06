import Foundation
import Vision
let root=URL(fileURLWithPath:CommandLine.arguments[1])
let metadata=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2]))) as! [String:[String:Any]]
for name in metadata.keys.sorted() {
 let url=root.appendingPathComponent(name)
 let output=url.deletingPathExtension().appendingPathExtension("columns.ocr.json")
 if FileManager.default.fileExists(atPath:output.path) {continue}
 let m=metadata[name]!;let xs=m["xs"] as! [Double];let ys=m["ys"] as! [Double]
 let w=m["width"]as! Double;let h=m["height"]as! Double
 var columns=[[[String:Any]]]()
 for col in 0..<12 {
  let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate
  request.recognitionLanguages = (col==0 || col==2 || col==8) ? ["en-US"] : ["zh-Hans","en-US"]
  request.usesLanguageCorrection = true
  request.regionOfInterest=CGRect(x:(xs[col]+2)/w,y:1-(ys.last!-2)/h,width:(xs[col+1]-xs[col]-4)/w,height:(ys.last!-ys[1]-4)/h)
  try VNImageRequestHandler(url:url).perform([request])
  columns.append((request.results ?? []).compactMap { item -> [String:Any]? in
   guard let candidate=item.topCandidates(1).first else{return nil}
   let b=item.boundingBox
   return ["text":candidate.string,"confidence":candidate.confidence,"x":b.minX,"y":b.minY,"w":b.width,"h":b.height]
  })
 }
 try JSONSerialization.data(withJSONObject:columns,options:[.sortedKeys]).write(to:output)
 print(name,columns.reduce(0){$0+$1.count});fflush(stdout)
}
