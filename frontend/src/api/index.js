import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 120000,  // 腾讯视频等平台解析较慢，需要更长超时
})

// 请求拦截：自动带上 Token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一处理错误
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const detail = err.response?.data?.detail
    let msg = '网络错误'
    if (typeof detail === 'string') {
      msg = detail
    } else if (Array.isArray(detail)) {
      msg = detail.map(d => d.msg || JSON.stringify(d)).join('; ')
    } else if (detail && typeof detail === 'object') {
      msg = detail.msg || detail.message || JSON.stringify(detail)
    }
    return Promise.reject(new Error(msg))
  }
)

export default {
  // 认证
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data),
  getMe: () => http.get('/auth/me'),

  // 视频解析和下载
  getInfo: (url) => http.post('/info', { url }),
  download: (data) => http.post('/download', data),

  // 历史记录
  getHistory: () => http.get('/history'),

  // Cookies
  uploadCookies: (file) => {
    const form = new FormData()
    form.append('file', file)
    return http.post('/cookies/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  getCookiesStatus: () => http.get('/cookies/status'),

  // Bilibili SESSDATA
  setBiliSessdata: (sessdata) => http.post('/bilibili/sessdata', { sessdata }),
  getBiliSessdata: () => http.get('/bilibili/sessdata'),

  // 平台状态
  getPlatforms: () => http.get('/platforms'),
}
