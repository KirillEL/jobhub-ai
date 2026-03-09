import { createContext, useContext, useEffect, useMemo, useState } from 'react'

export type Locale = 'ru' | 'en'

interface TranslationDictionary {
  [key: string]: string | TranslationDictionary
}

type TranslationValue = string | TranslationDictionary

const STORAGE_KEY = 'vacancy-radar-locale'

const messages: Record<Locale, TranslationDictionary> = {
  ru: {
    app: {
      loadingTitle: 'Проверяем сессию...',
      loadingSubtitle: 'Подготавливаем рабочее пространство.',
      mainMenu: 'Главное меню',
      platformMode: 'Режим платформы',
      light: 'Светлая',
      dark: 'Темная',
      toggleTheme: 'Переключить тему',
      language: 'Язык',
      brandSubtitle: 'Редакция для SMB-продаж',
      notAuthorized: 'Не авторизован',
      logout: 'Выйти',
      nav: {
        dashboard: 'Дашборд',
        onboarding: 'Онбординг',
        jobs: 'Задачи',
        vacancies: 'Вакансии',
        insights: 'Инсайты',
        chat: 'AI-чат',
        settings: 'Настройки',
      },
    },
    common: {
      close: 'Закрыть',
      cancel: 'Отмена',
      confirm: 'Подтвердить',
      processing: 'Выполняем...',
      unknown: 'Неизвестно',
      notSpecified: 'Не указано',
      notSpecifiedMasc: 'Не указан',
      notSpecifiedFem: 'Не указана',
      openInNewTab: 'Открыть в новой вкладке',
      goToVacancy: 'Перейти к вакансии',
      selected: 'Выбрано',
      open: 'Открыть',
      exportCsvPage: 'Экспорт CSV (страница)',
      exportCsvAll: 'Экспорт CSV (все по фильтрам)',
      exportInProgress: 'Экспортируем...',
      previous: 'Назад',
      next: 'Вперед',
      apply: 'Применить',
      resultLabel: 'Результаты',
      pageLabel: 'Страница',
      id: 'ID',
      exportMode: 'Режим экспорта',
      exportModeVisible: 'Только видимые колонки',
      exportModeFull: 'Полный набор полей',
      yes: 'Да',
      no: 'Нет',
    },
    salary: {
      from: 'от',
      to: 'до',
    },
    auth: {
      badge: 'Платформа для продаж',
      heroTitle: 'Показывайте клиентам рынок найма в одном аккуратном интерфейсе',
      heroSubtitle:
        'JobHub объединяет сбор вакансий, рыночную аналитику и экспорт клиентских отчетов. Вход занимает минуту, ценность видна уже на первом дашборде.',
      meta1: 'Быстрый запуск',
      meta2: 'KPI для бизнеса',
      meta3: 'Экспорт в CSV/JSON',
      stat1Title: '5 min',
      stat1Text: 'До первой ценности',
      stat2Title: 'Live',
      stat2Text: 'Обновление сигналов рынка',
      stat3Title: 'B2B',
      stat3Text: 'Готово к клиентским демо',
      toastRegisterSuccessTitle: 'Профиль создан',
      toastRegisterSuccessText: 'Вы успешно зарегистрировались и вошли в систему.',
      toastLoginSuccessTitle: 'Вход выполнен',
      toastLoginSuccessText: 'Добро пожаловать!',
      toastRegisterErrorTitle: 'Ошибка регистрации',
      toastLoginErrorTitle: 'Ошибка входа',
      toastAuthErrorText: 'Проверьте данные и повторите попытку.',
      form: {
        registerPill: 'Новый аккаунт',
        loginPill: 'Вход в платформу',
        registerTitle: 'Создайте аккаунт и начните анализ',
        loginTitle: 'С возвращением в JobHub',
        registerHint: 'После регистрации вы сразу попадете в рабочее пространство аналитики.',
        loginHint: 'Войдите, чтобы запускать парсинг и отслеживать динамику найма.',
        email: 'Email',
        name: 'Имя',
        password: 'Пароль',
        namePlaceholder: 'Как к вам обращаться',
        hidePassword: 'Скрыть пароль',
        showPassword: 'Показать пароль',
        waiting: 'Подождите...',
        createAccount: 'Создать аккаунт',
        loginButton: 'Войти в систему',
        haveAccount: 'У меня уже есть аккаунт',
        createAccountSecondary: 'Создать аккаунт',
      },
    },
    dashboard: {
      title: 'Главная панель',
      subtitle: 'Ключевые показатели продукта и статуса данных для клиентского демо.',
      totalVacancies: 'Всего вакансий',
      activeFilters: 'Активных фильтров',
      currentPage: 'Страница',
      service: 'Сервис',
      serviceState: {
        ok: 'OK',
        checking: 'Проверка',
        degraded: 'С деградацией',
      },
      profileTitle: 'Клиентский профиль',
      account: 'Аккаунт',
      recentJobs: 'Последние задачи парсинга',
      pipelineUpdating: 'Статус конвейера: обновление...',
      pipelineCurrent: 'Статус конвейера: актуально',
      topCompanies: 'Топ компаний',
      topSkills: 'Топ навыков',
    },
    jobs: {
      title: 'Задачи',
      subtitle: 'Управляйте прогоном парсинга и отслеживайте статус задач.',
      newJob: 'Новая задача парсинга',
      query: 'Запрос',
      pages: 'Страниц',
      run: 'Запустить парсинг',
      running: 'Запускаем...',
      loadingTitle: 'Идет парсинг вакансий',
      loadingDescription: 'Собираем данные по рынку и подготавливаем результаты для таблицы и инсайтов.',
      loadingHint: 'Обычно это занимает до пары минут в зависимости от запроса и количества страниц.',
      history: 'История запусков',
      emptyTitle: 'История пока пустая',
      emptyDescription: 'Запустите первую задачу парсинга, чтобы увидеть динамику.',
    },
    insights: {
      title: 'Инсайты',
      subtitle: 'Бизнес-сигналы по спросу компаний и навыков.',
      topCompanies: 'Топ компаний',
      topSkills: 'Топ навыков',
      emptyTitle: 'Нет данных',
      emptyCompaniesDescription: 'Запустите парсинг, чтобы увидеть срез по компаниям.',
      emptySkillsDescription: 'Рыночные навыки появятся после первого запуска.',
    },
    chat: {
      title: 'AI-чат',
      subtitle: 'Будущая рабочая зона для общения с обученным RAG-ассистентом по вашим вакансиям и рынку.',
      status: 'Функция в разработке',
      headline: 'Здесь появится умный чат с RAG',
      description:
        'Мы готовим отдельный интерфейс, где можно будет задавать вопросы по собранным вакансиям, получать краткие выводы, сравнивать рынок и быстро собирать ответы для клиентов.',
      hint: 'Страница уже зарезервирована, чтобы вы могли заранее встроить её в продукт и навигацию.',
      primaryCta: 'Перейти к вакансиям',
      secondaryCta: 'Запустить новый парсинг',
      roadmapTitle: 'Что планируется',
      roadmap1: 'Ответы по вашей базе вакансий с опорой на RAG-контекст.',
      roadmap2: 'Сводки по ролям, компаниям, зарплатам и навыкам в формате “спросили -> получили ответ”.',
      roadmap3: 'Быстрые клиентские инсайты и подготовка текста для презентаций.',
    },
    onboarding: {
      title: 'Онбординг',
      subtitle: 'Покажите ценность платформы клиенту за первые 5 минут.',
      cta: 'Перейти к запуску парсинга',
      step1Title: 'Шаг 1. Настройте контекст поиска',
      step1Text: 'Выберите ключевые роли, города и уровень специалистов, которые важны для клиента.',
      step2Title: 'Шаг 2. Запустите первую задачу парсинга',
      step2Text: 'Система соберет рынок вакансий и сформирует стартовые KPI для разговора с заказчиком.',
      step3Title: 'Шаг 3. Подготовьте экспорт',
      step3Text: 'Сохраните результаты в CSV или JSON и отправьте клиенту вместе с выводами.',
    },
    settings: {
      title: 'Настройки',
      subtitle: 'Управление профилем, темой и безопасной очисткой данных.',
      profile: 'Профиль',
      email: 'Email',
      name: 'Имя',
      save: 'Сохранить',
      saving: 'Сохраняем...',
      appearance: 'Внешний вид',
      currentTheme: 'Текущая тема',
      light: 'Светлая',
      dark: 'Темная',
      data: 'Данные',
      cleanupDescription: 'Безопасное удаление всех вакансий текущего аккаунта.',
      cleanup: 'Очистить мои данные',
      profileSaved: 'Профиль сохранен.',
      profileUpdateFailed: 'Не удалось обновить профиль.',
      cleanupDone: 'Данные очищены. Удалено вакансий: {{count}}.',
      cleanupFailed: 'Не удалось удалить данные.',
      cleanupModalTitle: 'Подтвердите удаление',
      cleanupModalText: 'Это удалит все вакансии вашего аккаунта без возможности восстановления.',
      cleanupModalConfirm: 'Удалить',
    },
    vacancies: {
      title: 'Вакансии',
      subtitle: 'Фильтрация и просмотр клиентского рынка вакансий.',
      filters: {
        search: 'Поиск',
        city: 'Город',
        experience: 'Опыт',
        limit: 'Лимит',
        searchPlaceholder: 'python, golang, analytics',
        cityPlaceholder: 'Москва',
        experiencePlaceholder: '1-3, 3-6',
      },
      table: {
        title: 'Вакансия',
        company: 'Компания',
        city: 'Город',
        salary: 'Зарплата',
        details: 'Детали',
      },
      preview: {
        selectTitle: 'Выберите вакансию',
        selectDescription: 'Кликните по строке в таблице, чтобы увидеть подробности справа.',
        companyMissing: 'Компания не указана',
        city: 'Город',
        experience: 'Опыт',
        schedule: 'График',
        salary: 'Зарплата',
        publishDate: 'Дата публикации',
        sourceLink: 'Ссылка на источник',
        descriptionTitle: 'Описание вакансии',
        descriptionMissing: 'Описание вакансии недоступно в источнике.',
      },
      emptyTitle: 'Ничего не найдено',
      emptyDescription: 'Измените фильтры или запустите новый сбор вакансий в разделе Jobs.',
      exportPreparing: 'Подготовка экспорта...',
      exportProgress: 'Экспортируем: {{current}}/{{total}} ({{percent}}%)',
      exportDone: 'Готово: экспортировано {{count}} записей.',
      exportError: 'Ошибка экспорта: {{message}}',
      csv: {
        visibleHeaders: 'Вакансия,Компания,Город,Зарплата',
        fullHeaders: 'ID,Вакансия,Компания,Город,Зарплата,Опыт,График,Ссылка',
      },
    },
    errors: {
      validation: {
        emailRequired: 'Введите email.',
        emailInvalid: 'Введите корректный email.',
        passwordRequired: 'Введите пароль.',
        passwordShort: 'Пароль должен быть не короче 8 символов.',
        passwordLong: 'Пароль не должен быть длиннее 128 символов.',
        fullNameShort: 'Имя должно содержать минимум 2 символа.',
        fullNameLong: 'Имя не должно быть длиннее 120 символов.',
        queryRequired: 'Укажите поисковый запрос.',
        queryShort: 'Запрос должен содержать минимум 2 символа.',
        queryLong: 'Запрос не должен превышать 120 символов.',
        pagesInteger: 'Количество страниц должно быть целым числом.',
        pagesRange: 'Количество страниц должно быть от 1 до 20.',
        limitInteger: 'Лимит должен быть целым числом.',
        limitRange: 'Лимит на странице должен быть от 1 до 500.',
        optionalMax: '{{label}} не должно превышать {{max}} символов.',
      },
      common: {
        notAuthenticated: 'Пользователь не авторизован.',
      },
      hooks: {
        jobsLoadFailed: 'Не удалось загрузить историю запусков.',
        insightsLoadFailed: 'Не удалось загрузить рыночную аналитику.',
        vacanciesLoadFailed: 'Не удалось загрузить вакансии.',
      },
      api: {
        requestCancelled: 'Запрос отменен',
        requestTimedOut: '{{fallback}}. Время ожидания запроса истекло.',
        registrationFailed: 'Не удалось зарегистрироваться',
        loginFailed: 'Не удалось выполнить вход',
        sessionRefreshFailed: 'Не удалось обновить сессию',
        logoutFailed: 'Не удалось выполнить выход',
        profileFetchFailed: 'Не удалось загрузить профиль',
        profileUpdateFailed: 'Не удалось обновить профиль',
        parseRequestFailed: 'Не удалось запустить парсинг',
        parseJobStatusFailed: 'Не удалось загрузить статус задачи',
        parseJobsFailed: 'Не удалось загрузить список задач',
        healthCheckFailed: 'Не удалось проверить состояние сервиса',
        vacanciesFailed: 'Не удалось загрузить вакансии',
        insightsFailed: 'Не удалось загрузить инсайты',
        vacancyCleanupFailed: 'Не удалось очистить вакансии',
      },
    },
    health: {
      checking: 'Проверяем стабильность API...',
      stable: 'Сервис работает стабильно.',
      degraded: 'Есть деградация: API {{api}}, DB {{db}}.',
      unavailable: 'Сервис временно недоступен, проверьте соединение с API.',
    },
    status: {
      job: {
        pending: 'Ожидает',
        running: 'Выполняется',
        done: 'Завершено',
        failed: 'Ошибка',
      },
    },
  },
  en: {
    app: {
      loadingTitle: 'Checking session...',
      loadingSubtitle: 'Preparing your workspace.',
      mainMenu: 'Main menu',
      platformMode: 'Platform mode',
      light: 'Light',
      dark: 'Dark',
      toggleTheme: 'Toggle theme',
      language: 'Language',
      brandSubtitle: 'SMB Sales Edition',
      notAuthorized: 'Not authorized',
      logout: 'Log out',
      nav: {
        dashboard: 'Dashboard',
        onboarding: 'Onboarding',
        jobs: 'Jobs',
        vacancies: 'Vacancies',
        insights: 'Insights',
        chat: 'AI Chat',
        settings: 'Settings',
      },
    },
    common: {
      close: 'Close',
      cancel: 'Cancel',
      confirm: 'Confirm',
      processing: 'Processing...',
      unknown: 'Unknown',
      notSpecified: 'Not specified',
      notSpecifiedMasc: 'Not specified',
      notSpecifiedFem: 'Not specified',
      openInNewTab: 'Open in a new tab',
      goToVacancy: 'Open vacancy',
      selected: 'Selected',
      open: 'Open',
      exportCsvPage: 'Export CSV (page)',
      exportCsvAll: 'Export CSV (all by filters)',
      exportInProgress: 'Exporting...',
      previous: 'Previous',
      next: 'Next',
      apply: 'Apply',
      resultLabel: 'Results',
      pageLabel: 'Page',
      id: 'ID',
      exportMode: 'Export mode',
      exportModeVisible: 'Visible columns only',
      exportModeFull: 'Full field set',
      yes: 'Yes',
      no: 'No',
    },
    salary: {
      from: 'from',
      to: 'up to',
    },
    auth: {
      badge: 'Sales-Ready Platform',
      heroTitle: 'Show clients the hiring market in one polished interface',
      heroSubtitle:
        'JobHub combines vacancy collection, market analytics, and client-ready exports. Sign-in takes a minute, and value is visible on the first dashboard.',
      meta1: 'Fast onboarding',
      meta2: 'Business KPIs',
      meta3: 'CSV/JSON export',
      stat1Title: '5 min',
      stat1Text: 'To first value',
      stat2Title: 'Live',
      stat2Text: 'Market signals refresh',
      stat3Title: 'B2B UX',
      stat3Text: 'Ready for client demos',
      toastRegisterSuccessTitle: 'Profile created',
      toastRegisterSuccessText: 'You have successfully registered and signed in.',
      toastLoginSuccessTitle: 'Signed in',
      toastLoginSuccessText: 'Welcome back!',
      toastRegisterErrorTitle: 'Registration error',
      toastLoginErrorTitle: 'Login error',
      toastAuthErrorText: 'Check your credentials and try again.',
      form: {
        registerPill: 'New account',
        loginPill: 'Platform sign in',
        registerTitle: 'Create an account and start analyzing',
        loginTitle: 'Welcome back to JobHub',
        registerHint: 'After registration you will enter the analytics workspace immediately.',
        loginHint: 'Sign in to launch parsing and track hiring trends.',
        email: 'Email',
        name: 'Name',
        password: 'Password',
        namePlaceholder: 'How should we address you',
        hidePassword: 'Hide password',
        showPassword: 'Show password',
        waiting: 'Please wait...',
        createAccount: 'Create account',
        loginButton: 'Log in to dashboard',
        haveAccount: 'I already have an account',
        createAccountSecondary: 'Create account',
      },
    },
    dashboard: {
      title: 'Executive Dashboard',
      subtitle: 'Key product and data health metrics for client demos.',
      totalVacancies: 'Total vacancies',
      activeFilters: 'Active filters',
      currentPage: 'Page',
      service: 'Service',
      serviceState: {
        ok: 'OK',
        checking: 'Checking',
        degraded: 'Degraded',
      },
      profileTitle: 'Client profile',
      account: 'Account',
      recentJobs: 'Recent parsing jobs',
      pipelineUpdating: 'Pipeline status: updating...',
      pipelineCurrent: 'Pipeline status: current',
      topCompanies: 'Top companies',
      topSkills: 'Top skills',
    },
    jobs: {
      title: 'Jobs',
      subtitle: 'Manage parsing runs and monitor job status.',
      newJob: 'New parsing job',
      query: 'Query',
      pages: 'Pages',
      run: 'Run parsing',
      running: 'Launching...',
      loadingTitle: 'Parsing vacancies',
      loadingDescription: 'We are collecting market data and preparing results for the table and insights.',
      loadingHint: 'This usually takes up to a couple of minutes depending on the query and page count.',
      history: 'Run history',
      emptyTitle: 'History is empty',
      emptyDescription: 'Launch the first parsing job to see activity here.',
    },
    insights: {
      title: 'Insights',
      subtitle: 'Business signals for demand across companies and skills.',
      topCompanies: 'Top companies',
      topSkills: 'Top skills',
      emptyTitle: 'No data',
      emptyCompaniesDescription: 'Run parsing to see a company snapshot.',
      emptySkillsDescription: 'Market skills will appear after the first run.',
    },
    chat: {
      title: 'AI Chat',
      subtitle: 'A future workspace for talking to a trained RAG assistant about your vacancies and market data.',
      status: 'Feature in development',
      headline: 'A smart RAG chat will appear here',
      description:
        'We are preparing a dedicated interface where users will ask questions about collected vacancies, get concise takeaways, compare market signals, and prepare client-ready answers faster.',
      hint: 'This page is already reserved so you can introduce it in the product and navigation ahead of launch.',
      primaryCta: 'Open vacancies',
      secondaryCta: 'Run a new parsing job',
      roadmapTitle: 'What is planned',
      roadmap1: 'Answers grounded in your vacancy database using RAG context.',
      roadmap2: 'Role, company, salary, and skill summaries in a simple ask-and-answer flow.',
      roadmap3: 'Fast client insights and draft text for presentations.',
    },
    onboarding: {
      title: 'Onboarding',
      subtitle: 'Show platform value to a client in the first 5 minutes.',
      cta: 'Go to parsing launch',
      step1Title: 'Step 1. Define the search context',
      step1Text: 'Choose the roles, cities, and seniority levels that matter for the client.',
      step2Title: 'Step 2. Launch the first parsing job',
      step2Text: 'The system will collect the market and prepare starter KPIs for the client conversation.',
      step3Title: 'Step 3. Prepare the export',
      step3Text: 'Save results to CSV or JSON and send them with your conclusions.',
    },
    settings: {
      title: 'Settings',
      subtitle: 'Manage profile, theme, and safe data cleanup.',
      profile: 'Profile',
      email: 'Email',
      name: 'Name',
      save: 'Save',
      saving: 'Saving...',
      appearance: 'Appearance',
      currentTheme: 'Current theme',
      light: 'Light',
      dark: 'Dark',
      data: 'Data',
      cleanupDescription: 'Safely remove all vacancies from the current account.',
      cleanup: 'Clear my data',
      profileSaved: 'Profile saved.',
      profileUpdateFailed: 'Failed to update profile.',
      cleanupDone: 'Data cleared. Removed vacancies: {{count}}.',
      cleanupFailed: 'Failed to delete data.',
      cleanupModalTitle: 'Confirm deletion',
      cleanupModalText: 'This will delete all vacancies in your account and cannot be undone.',
      cleanupModalConfirm: 'Delete',
    },
    vacancies: {
      title: 'Vacancies',
      subtitle: 'Filter and explore the client-facing vacancy market.',
      filters: {
        search: 'Search',
        city: 'City',
        experience: 'Experience',
        limit: 'Limit',
        searchPlaceholder: 'python, golang, analytics',
        cityPlaceholder: 'London',
        experiencePlaceholder: '1-3, 3-6',
      },
      table: {
        title: 'Vacancy',
        company: 'Company',
        city: 'City',
        salary: 'Salary',
        details: 'Details',
      },
      preview: {
        selectTitle: 'Select a vacancy',
        selectDescription: 'Click a row in the table to view details on the right.',
        companyMissing: 'Company not specified',
        city: 'City',
        experience: 'Experience',
        schedule: 'Schedule',
        salary: 'Salary',
        publishDate: 'Publish date',
        sourceLink: 'Source link',
        descriptionTitle: 'Vacancy description',
        descriptionMissing: 'Vacancy description is not available from the source.',
      },
      emptyTitle: 'Nothing found',
      emptyDescription: 'Adjust filters or start a new data collection run in Jobs.',
      exportPreparing: 'Preparing export...',
      exportProgress: 'Exporting: {{current}}/{{total}} ({{percent}}%)',
      exportDone: 'Done: exported {{count}} records.',
      exportError: 'Export error: {{message}}',
      csv: {
        visibleHeaders: 'Vacancy,Company,City,Salary',
        fullHeaders: 'ID,Vacancy,Company,City,Salary,Experience,Schedule,Link',
      },
    },
    errors: {
      validation: {
        emailRequired: 'Enter an email.',
        emailInvalid: 'Enter a valid email.',
        passwordRequired: 'Enter a password.',
        passwordShort: 'Password must be at least 8 characters long.',
        passwordLong: 'Password must not exceed 128 characters.',
        fullNameShort: 'Name must contain at least 2 characters.',
        fullNameLong: 'Name must not exceed 120 characters.',
        queryRequired: 'Enter a search query.',
        queryShort: 'Query must contain at least 2 characters.',
        queryLong: 'Query must not exceed 120 characters.',
        pagesInteger: 'Page count must be an integer.',
        pagesRange: 'Page count must be between 1 and 20.',
        limitInteger: 'Limit must be an integer.',
        limitRange: 'Per-page limit must be between 1 and 500.',
        optionalMax: '{{label}} must not exceed {{max}} characters.',
      },
      common: {
        notAuthenticated: 'User is not authenticated.',
      },
      hooks: {
        jobsLoadFailed: 'Failed to load run history.',
        insightsLoadFailed: 'Failed to load market insights.',
        vacanciesLoadFailed: 'Failed to load vacancies.',
      },
      api: {
        requestCancelled: 'Request cancelled',
        requestTimedOut: '{{fallback}}. Request timed out.',
        registrationFailed: 'Registration failed',
        loginFailed: 'Login failed',
        sessionRefreshFailed: 'Session refresh failed',
        logoutFailed: 'Logout failed',
        profileFetchFailed: 'Profile fetch failed',
        profileUpdateFailed: 'Profile update failed',
        parseRequestFailed: 'Parse request failed',
        parseJobStatusFailed: 'Fetch parse job status failed',
        parseJobsFailed: 'Fetch parse jobs failed',
        healthCheckFailed: 'Health check failed',
        vacanciesFailed: 'Fetch vacancies failed',
        insightsFailed: 'Fetch insights failed',
        vacancyCleanupFailed: 'Vacancy cleanup failed',
      },
    },
    health: {
      checking: 'Checking API stability...',
      stable: 'Service is running normally.',
      degraded: 'Degradation detected: API {{api}}, DB {{db}}.',
      unavailable: 'Service is temporarily unavailable. Check API connectivity.',
    },
    status: {
      job: {
        pending: 'Pending',
        running: 'Running',
        done: 'Done',
        failed: 'Failed',
      },
    },
  },
}

let currentLocale: Locale = 'ru'

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'ru'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return stored === 'en' ? 'en' : 'ru'
}

function getNestedValue(dictionary: TranslationDictionary, path: string): TranslationValue | undefined {
  return path.split('.').reduce<TranslationValue | undefined>((accumulator, key) => {
    if (!accumulator || typeof accumulator === 'string') return undefined
    return accumulator[key]
  }, dictionary)
}

export function hasTranslation(key: string, locale: Locale = currentLocale): boolean {
  return typeof getNestedValue(messages[locale], key) === 'string'
}

export function translate(
  key: string,
  params?: Record<string, string | number>,
  locale: Locale = currentLocale,
): string {
  const value = getNestedValue(messages[locale], key)
  if (typeof value !== 'string') return key
  if (!params) return value
  return value.replace(/\{\{(\w+)\}\}/g, (_, token: string) => String(params[token] ?? ''))
}

export function setGlobalLocale(locale: Locale): void {
  currentLocale = locale
}

export function translateJobStatus(status: string, locale: Locale = currentLocale): string {
  const key = `status.job.${status}`
  return hasTranslation(key, locale) ? translate(key, undefined, locale) : status
}

interface I18nContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string, params?: Record<string, string | number>) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale)

  useEffect(() => {
    setGlobalLocale(locale)
    window.localStorage.setItem(STORAGE_KEY, locale)
  }, [locale])

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale: setLocaleState,
      t: (key, params) => translate(key, params, locale),
    }),
    [locale],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useI18n must be used inside I18nProvider')
  }
  return context
}
