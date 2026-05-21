<template>
  <form class="calculator card" @submit.prevent="submit">
    <h2>Калькулятор вклада</h2>

    <div v-if="variant" class="calculator__selected">
      <div class="calculator__selected-title">Выбран вклад</div>
      <div class="calculator__selected-name">
        {{ bankName }} — {{ variantName }}
      </div>
      <div class="calculator__selected-meta">
        {{ selectedMetaLabel }}
      </div>
    </div>

    <div v-else-if="loading" class="calculator__placeholder">
      Загрузка параметров вклада...
    </div>

    <div v-else class="calculator__placeholder">
      Перейдите в калькулятор из карточки вклада.
    </div>

    <div class="calculator__grid">
      <UiInput
        v-model="form.amount"
        label="Сумма"
        type="number"
      />

      <UiSelect
        v-model="termValue"
        label="Срок вклада"
        :options="termOptions"
      />

      <UiInput
        v-model="form.promo_code"
        label="Промокод"
      />

      <UiSelect
        v-model="form.open_method_code"
        label="Способ открытия"
        :options="openMethodOptions"
      />

      <UiSelect
        v-model="form.interest_scheme_code"
        label="Начисление процентов"
        :options="interestSchemeOptions"
      />

      <UiSelect
        v-model="form.customer_segment_code"
        label="Сегмент клиента"
        :options="customerSegmentOptions"
      />
    </div>

    <div class="calculator__checks">
      <UiCheckbox v-model="form.has_subscription" label="Есть подписка" />
      <UiCheckbox v-model="form.is_salary_client" label="Зарплатный клиент" />
      <UiCheckbox v-model="form.is_pension_client" label="Пенсионный клиент" />
      <UiCheckbox v-model="form.has_premium_package" label="Премиум-пакет" />
    </div>

    <button
      class="btn btn-primary"
      type="submit"
      :disabled="!variant || !isReadyToSubmit"
    >
      Рассчитать доходность
    </button>
  </form>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import UiCheckbox from './UiCheckbox.vue'
import UiInput from './UiInput.vue'
import UiSelect from './UiSelect.vue'

const props = defineProps({
  variant: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit'])

const form = reactive({
  amount: '',
  term_days: '',
  open_method_code: '',
  interest_scheme_code: '',
  customer_segment_code: '',
  has_subscription: false,
  is_salary_client: false,
  is_pension_client: false,
  has_premium_package: false,
  promo_code: ''
})

const variantName = computed(() => props.variant?.name || 'Вклад')

const bankName = computed(() => {
  return (
    props.variant?.bank?.name ||
    props.variant?.product?.bank?.name ||
    props.variant?.product?.bank_name ||
    'Банк'
  )
})

const currencyCode = computed(() => props.variant?.product?.currency || 'RUB')
const minAmount = computed(() => props.variant?.min_amount ?? null)
const maxAmount = computed(() => props.variant?.max_amount ?? null)
const minTermDays = computed(() => Number(props.variant?.min_term_days || 0))
const maxTermDays = computed(() => Number(props.variant?.max_term_days || 0))

const amountLabel = computed(() => {
  if (minAmount.value == null) return '—'
  return formatMoneyWithCurrency(minAmount.value, currencyCode.value)
})

const maxAmountLabel = computed(() => {
  if (maxAmount.value == null) return ''
  return formatMoneyWithCurrency(maxAmount.value, currencyCode.value)
})

const minTermLabel = computed(() => {
  return minTermDays.value ? formatDaysLabel(minTermDays.value) : '—'
})

const maxTermLabel = computed(() => {
  return maxTermDays.value ? formatDaysLabel(maxTermDays.value) : '—'
})

const selectedMetaLabel = computed(() => {
  const amountText = maxAmount.value != null
    ? `Сумма от ${amountLabel.value} до ${maxAmountLabel.value}`
    : `Сумма от ${amountLabel.value}`

  const termText = maxTermDays.value
    ? `срок от ${minTermLabel.value} до ${maxTermLabel.value}`
    : `срок от ${minTermLabel.value}`

  return `${amountText} · ${termText}`
})

function formatMoneyWithCurrency(value, currencyCode) {
  const amount = Number(value)

  if (Number.isNaN(amount)) {
    return `0 ${currencyCode}`
  }

  return `${new Intl.NumberFormat('ru-RU', {
    maximumFractionDigits: 2,
    minimumFractionDigits: amount % 1 === 0 ? 0 : 2
  }).format(amount)} ${currencyCode}`
}

function payoutShortLabel(code) {
  const map = {
    end_of_term: 'В конце срока',
    end: 'В конце срока',
    monthly: 'Ежемесячно',
    quarterly: 'Ежеквартально',
    yearly: 'Ежегодно',
    daily: 'Ежедневно'
  }
  return map[code] || code || 'Не указано'
}

function schemeLabel(scheme) {
  if (!scheme) return 'Не указано'

  if (scheme.name) {
    return scheme.name
  }

  const payout = payoutShortLabel(scheme.payout_type)
  return scheme.capitalization_enabled ? `${payout} с капитализацией` : payout
}

function openMethodLabel(method) {
  if (!method) return 'Не указано'
  if (method.name) return method.name

  const map = {
    online: 'Онлайн',
    office: 'В отделении банка',
    branch: 'В отделении банка',
    mobile_app: 'В мобильном приложении',
    internet_bank: 'В интернет-банке',
    gosuslugi: 'Через Госуслуги',
    out_of_office_worker: 'Работник банка вне офиса'
  }

  return map[method.code] || method.code || 'Не указано'
}

function dedupeByValue(items) {
  const map = new Map()

  items.forEach((item) => {
    if (!item?.value) return
    if (!map.has(item.value)) {
      map.set(item.value, item)
    }
  })

  return [...map.values()]
}

function currentAmount() {
  const amount = Number(form.amount)
  if (Number.isFinite(amount) && amount > 0) return amount
  return Number(props.variant?.min_amount || 0)
}

function rateMatchesAmount(rate) {
  const amount = currentAmount()
  if (!amount) return true

  const from = Number(rate.amount_from || 0)
  const to = rate.amount_to == null ? null : Number(rate.amount_to)

  return amount >= from && (to == null || amount <= to)
}

function rateMatchesSelectedMethod(rate) {
  if (!form.open_method_code) return true

  // null в ставке означает универсальную ставку для любого способа открытия.
  if (!rate.open_method_id && !rate.open_method?.code) return true

  return rate.open_method?.code === form.open_method_code
}

function rateMatchesSelectedScheme(rate) {
  if (!form.interest_scheme_code) return true

  // null в ставке означает универсальную ставку для любой схемы начисления.
  if (!rate.interest_scheme_id && !rate.interest_scheme?.code) return true

  return rate.interest_scheme?.code === form.interest_scheme_code
}

function rateMatchesSelectedSegment(rate) {
  const selected = form.customer_segment_code || ''
  const rateSegment = rate.customer_segment?.code || ''

  // Для обычного клиента показываем только универсальные ставки.
  if (!selected) {
    return !rateSegment || rateSegment === 'common'
  }

  // Для выбранного сегмента показываем ставки сегмента и универсальные ставки.
  return !rateSegment || rateSegment === 'common' || rateSegment === selected
}

function getRateFromDays(rate) {
  return Number(rate.term_from_days || 0)
}

function getRateToDays(rate) {
  return Number(rate.term_to_days || rate.term_from_days || 0)
}

function formatDaysLabel(days) {
  const value = Number(days)

  const known = {
    30: '1 месяц',
    31: '1 месяц',
    60: '2 месяца',
    61: '2 месяца',
    90: '3 месяца',
    91: '3 месяца',
    120: '4 месяца',
    150: '5 месяцев',
    180: '6 месяцев',
    181: '6 месяцев',
    182: '6 месяцев',
    183: '6 месяцев',
    210: '7 месяцев',
    212: '7 месяцев',
    240: '8 месяцев',
    243: '8 месяцев',
    270: '9 месяцев',
    273: '9 месяцев',
    300: '10 месяцев',
    304: '10 месяцев',
    330: '11 месяцев',
    334: '11 месяцев',
    360: '1 год',
    365: '1 год',
    367: '1 год',
    390: '13 месяцев',
    510: '17 месяцев',
    540: '1,5 года',
    548: '1,5 года',
    730: '2 года',
    1095: '3 года'
  }

  return known[value] || `${value} дн.`
}

function termLabel(from, to) {
  if (Number(from) === Number(to)) {
    return `${formatDaysLabel(from)} (${from} дн.)`
  }

  return `${formatDaysLabel(from)} — ${formatDaysLabel(to)} (${from}–${to} дн.)`
}

function buildTermOptions(baseRates, variant) {
  if (!variant) return []

  const rates = (baseRates || [])
    .map((rate) => ({
      from: getRateFromDays(rate),
      to: getRateToDays(rate)
    }))
    .filter((rate) => rate.from > 0 && rate.to >= rate.from)
    .sort((a, b) => a.from - b.from || a.to - b.to)

  if (!rates.length) {
    const fallback = Number(variant.min_term_days || 0)
    return fallback ? [{ value: String(fallback), label: `${formatDaysLabel(fallback)} (${fallback} дн.)` }] : []
  }

  const optionsByRange = new Map()

  rates.forEach((rate) => {
    const key = `${rate.from}-${rate.to}`
    if (!optionsByRange.has(key)) {
      optionsByRange.set(key, {
        value: String(rate.from),
        label: termLabel(rate.from, rate.to),
        from: rate.from,
        to: rate.to
      })
    }
  })

  return [...optionsByRange.values()]
    .sort((a, b) => a.from - b.from || a.to - b.to)
    .map(({ value, label }) => ({ value, label }))
}

const filteredRatesByMethodAndScheme = computed(() => {
  const rates = props.variant?.base_rates || []

  return rates.filter((rate) => {
    return (
      rateMatchesAmount(rate) &&
      rateMatchesSelectedMethod(rate) &&
      rateMatchesSelectedScheme(rate) &&
      rateMatchesSelectedSegment(rate)
    )
  })
})

const openMethodOptions = computed(() => {
  const methodsFromRates = (props.variant?.base_rates || [])
    .map((rate) => rate.open_method)
    .filter(Boolean)
    .map((method) => ({
      value: method.code,
      label: openMethodLabel(method)
    }))

  const methodsFromVariant = (props.variant?.open_methods || [])
    .filter(Boolean)
    .map((method) => ({
      value: method.code,
      label: openMethodLabel(method)
    }))

  const options = dedupeByValue([...methodsFromVariant, ...methodsFromRates])

  return options.length ? options : [{ value: '', label: 'Не указано' }]
})

const interestSchemeOptions = computed(() => {
  const schemesFromRates = (props.variant?.base_rates || [])
    .map((rate) => rate.interest_scheme)
    .filter(Boolean)
    .map((scheme) => ({
      value: scheme.code,
      label: schemeLabel(scheme)
    }))

  const schemesFromVariant = (props.variant?.interest_schemes || [])
    .filter(Boolean)
    .map((scheme) => ({
      value: scheme.code,
      label: schemeLabel(scheme)
    }))

  const options = dedupeByValue([...schemesFromVariant, ...schemesFromRates])

  return options.length ? options : [{ value: '', label: 'Не указано' }]
})

const customerSegmentOptions = computed(() => {
  const segments = (props.variant?.base_rates || [])
    .map((rate) => rate.customer_segment)
    .filter(Boolean)
    .map((segment) => ({
      value: segment.code,
      label: segment.name
    }))
    .filter((segment) => segment.value !== 'common')

  return [
    { value: '', label: 'Обычный клиент' },
    ...dedupeByValue(segments)
  ]
})

const termOptions = computed(() => {
  return buildTermOptions(filteredRatesByMethodAndScheme.value, props.variant)
})

const termValue = computed({
  get: () => String(form.term_days || ''),
  set: (value) => {
    form.term_days = value ? Number(value) : ''
  }
})

function chooseDefaultScheme(variant) {
  const schemes = variant?.interest_schemes || []
  const capitalized = schemes.find((scheme) => scheme?.capitalization_enabled === true)
  const firstFromOptions = interestSchemeOptions.value[0]?.value || ''
  return capitalized?.code || firstFromOptions
}

function setFirstAvailableTerm() {
  const firstTerm = termOptions.value[0]?.value
  form.term_days = firstTerm ? Number(firstTerm) : Number(props.variant?.min_term_days || 0)
}

watch(
  () => props.variant,
  (variant) => {
    if (!variant) return

    form.amount = Number(variant.min_amount || 0)
    form.open_method_code = openMethodOptions.value[0]?.value || ''
    form.interest_scheme_code = chooseDefaultScheme(variant)
    form.customer_segment_code = customerSegmentOptions.value[0]?.value || ''
    setFirstAvailableTerm()
  },
  { immediate: true }
)

watch(
  () => [form.open_method_code, form.interest_scheme_code, form.customer_segment_code, form.amount],
  () => {
    const availableTerms = termOptions.value
    if (!availableTerms.length) return

    const current = String(form.term_days || '')
    const exists = availableTerms.some((item) => item.value === current)

    if (!exists) {
      form.term_days = Number(availableTerms[0].value)
    }
  }
)

const isReadyToSubmit = computed(() => {
  return Boolean(
    props.variant &&
    Number(form.amount) > 0 &&
    Number(form.term_days) > 0
  )
})

function submit() {
  if (!props.variant) return

  emit('submit', {
    variant_id: Number(props.variant.id),
    amount: Number(form.amount),
    term_days: Number(form.term_days),
    open_method_code: form.open_method_code || null,
    interest_scheme_code: form.interest_scheme_code || null,
    customer_segment_code: form.customer_segment_code || null,
    conditions: {
      has_subscription: form.has_subscription,
      is_salary_client: form.is_salary_client,
      is_pension_client: form.is_pension_client,
      has_premium_package: form.has_premium_package
    },
    has_subscription: form.has_subscription,
    is_salary_client: form.is_salary_client,
    is_pension_client: form.is_pension_client,
    monthly_spend: null,
    savings_balance: null,
    has_premium_package: form.has_premium_package,
    promo_code: form.promo_code || null,
    extra_context: {}
  })
}
</script>

<style scoped>
.calculator {
  padding: 28px;
}

.calculator h2 {
  margin: 0 0 18px;
}

.calculator__selected {
  margin-bottom: 18px;
  padding: 18px 20px;
  border-radius: 20px;
  background: #f5fbff;
  border: 1px solid var(--border);
}

.calculator__selected-title {
  color: var(--text-soft);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
}

.calculator__selected-name {
  font-weight: 800;
  font-size: 18px;
  line-height: 1.25;
  letter-spacing: -0.025em;
  margin-bottom: 6px;
}

.calculator__placeholder {
  margin-bottom: 18px;
  padding: 16px 18px;
  border-radius: 18px;
  background: #fbfeff;
  border: 1px solid var(--border);
  color: var(--text-soft);
  font-weight: 500;
}

.calculator__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.calculator__checks {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

@media (max-width: 900px) {
  .calculator__grid,
  .calculator__checks {
    grid-template-columns: 1fr;
  }
}
</style>
