// 将 docs/1_高中英语词汇3500词(必背).doc 转换为结构化 JSON。
// 依赖 macOS 自带的 textutil 将 .doc 转为纯文本，再按行解析。
// 用法：node scripts/convert-vocab.js
const fs = require('fs')
const path = require('path')
const { execFileSync } = require('child_process')

const root = path.resolve(__dirname, '..')
const docPath = path.join(root, 'docs', '1_高中英语词汇3500词(必背).doc')
const txtPath = path.join(require('os').tmpdir(), 'vocab.txt')
const outPath = path.join(root, 'docs', 'EnglishVocabulary.json')

execFileSync('textutil', ['-convert', 'txt', '-output', txtPath, docPath])
const raw = fs.readFileSync(txtPath, 'utf8')
const lines = raw.split(/\r?\n/).map(l => l.trim()).filter(Boolean)

const POS_MAP = {
  v: '动词', vt: '动词', vi: '动词', aux: '动词', modal: '动词',
  n: '名词', a: '形容词', adj: '形容词', ad: '副词', adv: '副词',
  prep: '介词', conj: '连词', pron: '代词', num: '数词',
  art: '冠词', int: '感叹词', interj: '感叹词'
}

function posTag(meaning) {
  const match = meaning.match(/^([a-zA-Z]+)/)
  if (!match) return ''
  return POS_MAP[match[1].toLowerCase()] || ''
}

const words = []
let id = 0

for (const line of lines) {
  if (line === '高中英语词汇3500词') continue
  if (/^[A-Z]$/.test(line)) continue // 字母分节标题

  let word = ''
  let phonetic = ''
  let meaning = ''

  const open = line.indexOf('[')
  const close = line.indexOf(']')
  if (open !== -1 && close !== -1 && close > open) {
    word = line.slice(0, open).trim()
    phonetic = line.slice(open + 1, close).trim()
    meaning = line.slice(close + 1).trim()
  } else {
    // 少数词条用 /.../ 斜杠音标而非方括号
    const slash = line.match(/^(.+?)\s*\/\s*([^/]+?)\s*\/\s*(.+)$/)
    if (slash) {
      word = slash[1].trim()
      phonetic = slash[2].replace(/`/g, 'ˈ').trim()
      meaning = slash[3].trim()
    } else {
      const idx = line.indexOf(' ')
      if (idx === -1) continue
      word = line.slice(0, idx).trim()
      meaning = line.slice(idx + 1).trim()
    }
  }

  if (!word || !/[A-Za-z]/.test(word) || !meaning) continue

  words.push({
    id: ++id,
    word,
    phonetic,
    meaning,
    tag: posTag(meaning),
    letter: (word[0] || '#').toUpperCase()
  })
}

fs.writeFileSync(outPath, JSON.stringify({
  title: '英语核心 3500 词',
  source: '1_高中英语词汇3500词(必背).doc',
  count: words.length,
  words
}, null, 2))

console.log('已生成', words.length, '个单词 →', path.relative(root, outPath))
console.log('无音标条目:', words.filter(w => !w.phonetic).length)
console.log('示例:', JSON.stringify(words.slice(0, 2), null, 0))
