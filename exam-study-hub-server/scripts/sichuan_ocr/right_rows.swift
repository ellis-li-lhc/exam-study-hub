import Foundation
import Vision
import ImageIO
import CoreGraphics
let root=URL(fileURLWithPath:CommandLine.arguments[1])
let metadata=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[2]))) as! [String:[String:Any]]
for name in metadata.keys.sorted() {
 let url=root.appendingPathComponent(name),output=url.deletingPathExtension().appendingPathExtension("rightrows.ocr.json")
 if FileManager.default.fileExists(atPath:output.path) {continue}
 let m=metadata[name]!,xs=m["xs"] as! [Int],ys=m["ys"] as! [Int]
 let src=CGImageSourceCreateWithURL(url as CFURL,nil)!,im=CGImageSourceCreateImageAtIndex(src,0,nil)!
 var rows=[[[String:Any]]]()
 for row in 1..<ys.count-1 {
  let rect=CGRect(x:xs[9]+2,y:ys[row]+2,width:xs[12]-xs[9]-4,height:ys[row+1]-ys[row]-4)
  let crop=im.cropping(to:rect)!,w=crop.width*3,h=crop.height*3
  let ctx=CGContext(data:nil,width:w,height:h,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipLast.rawValue)!
  ctx.interpolationQuality = .high;ctx.draw(crop,in:CGRect(x:0,y:0,width:w,height:h))
  let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate
  request.recognitionLanguages=["zh-Hans","en-US"];request.usesLanguageCorrection=true
  try VNImageRequestHandler(cgImage:ctx.makeImage()!).perform([request])
  rows.append((request.results ?? []).compactMap{item -> [String:Any]? in
   guard let c=item.topCandidates(1).first else{return nil};let b=item.boundingBox
   return ["text":c.string,"confidence":c.confidence,"x":b.minX,"y":b.minY,"w":b.width,"h":b.height]
  })
 }
 try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]).write(to:output)
 print(name,rows.count);fflush(stdout)
}
