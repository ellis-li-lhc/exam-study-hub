import fs from 'node:fs/promises'
import path from 'node:path'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

const PROVINCES = [
  {
    key: 'jiangsu',
    name: '江苏',
    shortCode: 'js',
    provinceUrl: 'https://www.zikaoben.cn/zxks/js/',
    majorsUrl: 'https://www.zikaoben.cn/cate/tid-117',
  },
  {
    key: 'henan',
    name: '河南',
    shortCode: 'ha',
    provinceUrl: 'https://www.zikaoben.cn/zxks/ha/',
    majorsUrl: 'https://www.zikaoben.cn/cate/tid-122',
  },
]

function stripTags(input) {
  return input
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&mdash;/g, '—')
    .replace(/&ldquo;|&rdquo;/g, '"')
    .replace(/&rsquo;|&lsquo;/g, "'")
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim()
}

function decodeHtml(input) {
  return input
    .replace(/&nbsp;/g, ' ')
    .replace(/&mdash;/g, '—')
    .replace(/&ldquo;|&rdquo;/g, '"')
    .replace(/&rsquo;|&lsquo;/g, "'")
    .replace(/&amp;/g, '&')
    .trim()
}

function toAbsoluteUrl(url) {
  if (!url) return null
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('//')) return `https:${url}`
  if (url.startsWith('/')) return `https://www.zikaoben.cn${url}`
  return `https://www.zikaoben.cn/${url.replace(/^\.?\//, '')}`
}

async function fetchHtml(url) {
  try {
    const response = await fetch(url, {
      headers: {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    return response.text()
  } catch (error) {
    const psScript = `(Invoke-WebRequest -Uri '${url}' -UseBasicParsing).Content`
    const { stdout } = await execFileAsync(
      'powershell',
      ['-NoProfile', '-Command', psScript],
      { maxBuffer: 20 * 1024 * 1024 },
    )
    if (!stdout.trim()) {
      throw new Error(`Failed to fetch ${url}: ${error.message}`)
    }
    return stdout
  }
}

function parseProvincePage(html, province) {
  const signupMatch = html.match(/class="zxks_a_r_bmlink" href="([^"]+)"[^>]*>\s*<i[^>]*><\/i><p>正式报名入口<\/p>/)
  const schoolMajorMatch = html.match(/class="zxks_a_r_bmlink" href="([^"]+)"[^>]*>\s*<i[^>]*><\/i><p>院校专业查询<\/p>/)
  const noteMatch = html.match(/<div class="zxks_a_r_note">([\s\S]*?)<\/div>/)
  const signupDescMatch = html.match(/<div class="zxks_r_t_c">([\s\S]*?)<\/div>/)

  const hotSchools = Array.from(
    html.matchAll(/<li><a href="([^"]+)"><img[^>]*alt="([^"]+)"[^>]*\/><div class="zkyx_other_item_i"><p>([^<]+)<\/p><p>([^<]+)<\/p><\/div><\/a><\/li>/g),
  ).map((match) => ({
    name: decodeHtml(match[3]),
    badge: decodeHtml(match[4]),
    url: toAbsoluteUrl(match[1]),
    imageAlt: decodeHtml(match[2]),
  }))

  const latestNewsBlock = html.match(new RegExp(`<h2>${province.name}自考最新资讯<\\/h2><ul>([\\s\\S]*?)<\\/ul>`))
  const latestNews = latestNewsBlock
    ? Array.from(
        latestNewsBlock[1].matchAll(/<li><a href="([^"]+)" target="_blank">([\s\S]*?) <span>([\d-]+)<\/span><\/a><\/li>/g),
      ).map((match) => ({
        title: stripTags(match[2]),
        date: match[3],
        url: toAbsoluteUrl(match[1]),
      }))
    : []

  const cityBlock = html.match(/<div class='zxks_city_nav[\s\S]*?<h3>相关链接<\/h3>([\s\S]*?)<\/div>/)
  const cities = cityBlock
    ? Array.from(cityBlock[1].matchAll(/<li><a href="([^"]+)">([^<]+)<\/li>/g)).map((match) => ({
        name: decodeHtml(match[2]).replace(/自考$/, ''),
        label: decodeHtml(match[2]),
        url: toAbsoluteUrl(match[1]),
      }))
    : []

  return {
    province: province.name,
    provinceUrl: province.provinceUrl,
    signupUrl: signupMatch ? signupMatch[1] : null,
    schoolMajorUrl: schoolMajorMatch ? schoolMajorMatch[1] : province.majorsUrl,
    note: noteMatch ? stripTags(noteMatch[1]) : '',
    signupDescription: signupDescMatch ? stripTags(signupDescMatch[1]) : '',
    hotSchools,
    latestNews,
    cities,
  }
}

function parseMajorsPage(html, province) {
  const introMatch = html.match(/<div class="zy_list_content">([\s\S]*?)<\/div>/)
  const rows = Array.from(
    html.matchAll(
      /<tr><td>(\d+)<\/td><td><a href="([^"]+)" target="blank">([^<]+)<\/a><\/td><td>([^<]+)<\/td><td>([^<]+)<\/td><td>([^<]+)<\/td><td>([^<]+)<\/td><td>[\s\S]*?<\/i>\s*([^<]+)<\/td><\/tr>/g,
    ),
  )

  const majors = rows.map((match) => ({
    order: Number(match[1]),
    name: decodeHtml(match[3]),
    code: decodeHtml(match[4]),
    level: decodeHtml(match[5]),
    schools: decodeHtml(match[6])
      .split('、')
      .map((item) => item.trim())
      .filter(Boolean),
    examDirection: decodeHtml(match[7]),
    status: decodeHtml(match[8]),
    detailUrl: toAbsoluteUrl(match[2]),
  }))

  return {
    province: province.name,
    majorsUrl: province.majorsUrl,
    intro: introMatch ? stripTags(introMatch[1]) : '',
    majorCount: majors.length,
    majors,
  }
}

async function main() {
  const outputDir = path.join(process.cwd(), 'scraped-data')
  await fs.mkdir(outputDir, { recursive: true })

  const result = {
    sourceSite: 'https://www.zikaoben.cn/',
    scrapedAt: new Date().toISOString(),
    provinces: [],
  }

  for (const province of PROVINCES) {
    const [provinceHtml, majorsHtml] = await Promise.all([
      fetchHtml(province.provinceUrl),
      fetchHtml(province.majorsUrl),
    ])

    const provinceInfo = parseProvincePage(provinceHtml, province)
    const majorInfo = parseMajorsPage(majorsHtml, province)

    result.provinces.push({
      key: province.key,
      name: province.name,
      shortCode: province.shortCode,
      ...provinceInfo,
      majorCatalog: majorInfo,
    })
  }

  const outputPath = path.join(outputDir, 'zikaoben-js-ha.json')
  await fs.writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8')
  console.log(outputPath)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
