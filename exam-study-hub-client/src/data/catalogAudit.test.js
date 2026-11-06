import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {examMajors, subjectsForCategory, reconcileDiagnosticSubjects} from './majors.js'
import {activePlansForMajor, controlScoresForMajor, tuitionForMajorText} from './institutionQuality.js'
const read=name=>JSON.parse(readFileSync(new URL(`../../../exam-study-hub-server/scraped-data/${name}`,import.meta.url)))

test('两个修正专业采用官方经管类高数二科目',()=>{
 for(const code of ['yingyong-xinli','xinxi-guanli']){
  const major=examMajors.find(m=>m.code===code)
  assert.equal(major.category,'经济管理类')
  assert.deepEqual(subjectsForCategory(major.category),['政治','英语','高等数学（二）'])
 }
})

test('旧诊断更正第三科后保留公共科目及历史记录，并要求补诊',()=>{
 for(const [code,previous]of [['yingyong-xinli','教育理论'],['xinxi-guanli','高等数学（一）']]){
  const history={completed:true,subjectScores:{政治:93,英语:81,[previous]:112},submittedSubjects:['政治','英语',previous],answers:{old:'A'},knowledgeDetails:[{subject:'政治',score:93}]}
  const result=reconcileDiagnosticSubjects(history,examMajors.find(m=>m.code===code))
  assert.equal(result.requiresRetest,true);assert.equal(result.diagnostic.completed,false)
  assert.deepEqual(result.diagnostic.subjectScores,{政治:93,英语:81,'高等数学（二）':0})
  assert.deepEqual(result.diagnostic.submittedSubjects,['政治','英语'])
  assert.deepEqual(result.diagnostic.answers,history.answers);assert.deepEqual(result.diagnostic.knowledgeDetails,history.knowledgeDetails)
  assert.equal(history.completed,true)
 }
})

test('已按正确科目完成的诊断及其他专业无需重测',()=>{
 for(const code of ['yingyong-xinli','xinxi-guanli','gongshang-guanli']){
  const old={completed:true,subjectScores:{政治:90,英语:80,'高等数学（二）':100},submittedSubjects:['政治','英语','高等数学（二）']}
  const result=reconcileDiagnosticSubjects(old,examMajors.find(m=>m.code===code))
  assert.equal(result.requiresRetest,false);assert.equal(result.diagnostic.completed,true)
 }
})

test('同名异科类专业不能混入学费和省控线预览',()=>{
 const school={province:'chongqing',majorMatch:'exact',activeCatalogYear:2026,plans:[
  {year:2026,major_name:'网络与新媒体',category_name:'文史中医类',tuition_raw:'2800元/年'},
  {year:2026,major_name:'网络与新媒体',category_name:'艺术类',tuition_raw:'1000元/年'}
 ],controlScores:[{year:2025,category_name:'文史中医类',line_type:'省控线',score:182},{year:2025,category_name:'艺术类',line_type:'省控线',score:160}]}
 assert.equal(tuitionForMajorText(school,'网络与新媒体'),'2800元/年')
 assert.deepEqual(controlScoresForMajor(school,'网络与新媒体').map(r=>r.score),[182])
})

test('四川匹配使用11月二次计划，同年旧目录不重复计数',()=>{
 const current=read('sichuan-adult-current-plans.json'),historic=read('sichuan-adult-programs.json')
 assert.equal(current.length,1240);assert.equal(current.reduce((n,r)=>n+r.plan_count,0),49031)
 const school={province:'sichuan',majorMatch:'exact',activeCatalogYear:2026,activeCatalogRound:'2026年第二次公布',plans:[...historic,...current].filter(p=>p.institution_code==='010')}
 const law=activePlansForMajor(school,'法学')
 assert.equal(law.length,6);assert.equal(law.reduce((n,r)=>n+r.plan_count,0),119)
 assert.ok(law.every(p=>p.round==='2026年第二次公布'))
})
