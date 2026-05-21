<template>
  <aside class="filters card">
    <h3>Фильтры</h3>

    <div class="filters__grid">
      <UiInput v-model="localFilters.amount" label="Сумма" type="number" />

      <div class="filters__field">
        <div class="filters__label">Банк</div>

        <div v-if="banksLoading" class="filters__hint">Загрузка банков...</div>

        <div v-else class="filters__multiselect">
          <button
            class="filters__multiselect-button"
            type="button"
            @click="banksDropdownOpen = !banksDropdownOpen"
          >
            <span>{{ selectedBanksLabel }}</span>
            <span class="filters__multiselect-arrow" :class="{ 'is-open': banksDropdownOpen }">⌄</span>
          </button>

          <div v-if="banksDropdownOpen" class="filters__multiselect-menu">
            <button
              v-for="bank in banks"
              :key="bank.id"
              class="filters__bank-option"
              :class="{ 'is-selected': isBankSelected(bank.id) }"
              type="button"
              @click="toggleBank(bank.id)"
            >
              <span class="filters__bank-check">
                {{ isBankSelected(bank.id) ? '✓' : '' }}
              </span>
              <span>{{ bank.name }}</span>
            </button>

            <div v-if="!banks.length" class="filters__hint filters__hint--inside">
              Банки не найдены
            </div>

            <div v-if="banks.length" class="filters__multiselect-actions">
              <button
                class="filters__link-button"
                type="button"
                @click="selectAllBanks"
              >
                Выбрать все
              </button>

              <button
                class="filters__link-button"
                type="button"
                @click="clearBanks"
              >
                Сбросить
              </button>

              <button
                class="filters__ready-button"
                type="button"
                @click="banksDropdownOpen = false"
              >
                Готово
              </button>
            </div>
          </div>
        </div>
      </div>

      <UiSelect
          v-model="termValue"
          label="Срок вклада"
          :options="termOptions"
      />

      <UiSelect
          v-model="localFilters.currency"
          label="Валюта"
          :options="currencyOptions"
      />

      <UiSelect
          v-model="capitalizationValue"
          label="Капитализация"
          :options="triStateOptions"
      />

      <UiSelect
          v-model="topupValue"
          label="Пополнение"
          :options="triStateOptions"
      />

      <UiSelect
          v-model="partialValue"
          label="Частичное снятие"
          :options="triStateOptions"
      />

      <UiSelect
          v-model="prolongValue"
          label="Автопролонгация"
          :options="triStateOptions"
      />
    </div>

    <div class="filters__actions">
      <button class="btn btn-primary" @click="submit">Показать предложения</button>
      <button class="btn btn-secondary" @click="reset">Сбросить</button>
    </div>
  </aside>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import UiInput from './UiInput.vue'
import UiSelect from './UiSelect.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  banks: {
    type: Array,
    default: () => []
  },
  banksLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const currencyOptions = [
  { value: 'RUB', label: 'RUB — российский рубль' },
  { value: 'USD', label: 'USD — доллар США' },
  { value: 'EUR', label: 'EUR — евро' },
  { value: 'CNY', label: 'CNY — китайский юань' },
  { value: 'JPY', label: 'JPY — японская иена' }
]

const termOptions = [
  { value: '', label: 'Не важно' },
  { value: '30', label: '1 месяц (30 дней)' },
  { value: '60', label: '2 месяца (60 дней)' },
  { value: '90', label: '3 месяца (90 дней)' },
  { value: '180', label: '6 месяцев (180 дней)' },
  { value: '360', label: '1 год (360 дней)' },
  { value: '540', label: '1,5 года (540 дней)' },
  { value: '730', label: '2 года (730 дней)' },
  { value: '1095', label: '3 года (1095 дней)' }
]

const triStateOptions = [
  { value: '', label: 'Не важно' },
  { value: 'true', label: 'Да' },
  { value: 'false', label: 'Нет' }
]

const banksDropdownOpen = ref(false)

const localFilters = reactive({
  ...props.modelValue,
  bank_ids: Array.isArray(props.modelValue.bank_ids) ? [...props.modelValue.bank_ids] : []
})

watch(
    () => props.modelValue,
    (value) => {
      Object.assign(localFilters, {
        ...value,
        bank_ids: Array.isArray(value.bank_ids) ? [...value.bank_ids] : []
      })
    },
    { deep: true }
)

const selectedBanks = computed(() => {
  const selectedIds = new Set((localFilters.bank_ids || []).map(Number))
  return props.banks.filter((bank) => selectedIds.has(Number(bank.id)))
})

const selectedBanksLabel = computed(() => {
  if (!selectedBanks.value.length) {
    return 'Все банки'
  }

  if (selectedBanks.value.length === 1) {
    return selectedBanks.value[0].name
  }

  if (selectedBanks.value.length <= 2) {
    return selectedBanks.value.map((bank) => bank.name).join(', ')
  }

  return `Выбрано банков: ${selectedBanks.value.length}`
})

const mapToUi = (value) => (value === null || value === undefined ? '' : String(value))
const mapFromUi = (value) => (value === '' ? null : value === 'true')

const capitalizationValue = computed({
  get: () => mapToUi(localFilters.capitalization_enabled),
  set: (value) => {
    localFilters.capitalization_enabled = mapFromUi(value)
  }
})

const topupValue = computed({
  get: () => mapToUi(localFilters.allow_topup),
  set: (value) => {
    localFilters.allow_topup = mapFromUi(value)
  }
})

const partialValue = computed({
  get: () => mapToUi(localFilters.allow_partial_withdraw),
  set: (value) => {
    localFilters.allow_partial_withdraw = mapFromUi(value)
  }
})

const prolongValue = computed({
  get: () => mapToUi(localFilters.auto_prolongation),
  set: (value) => {
    localFilters.auto_prolongation = mapFromUi(value)
  }
})

const termValue = computed({
  get: () => mapToUi(localFilters.term_days),
  set: (value) => {
    localFilters.term_days = value === '' ? null : Number(value)
  }
})

function isBankSelected(bankId) {
  return (localFilters.bank_ids || []).map(Number).includes(Number(bankId))
}

function toggleBank(bankId) {
  const normalizedId = Number(bankId)
  const selectedIds = new Set((localFilters.bank_ids || []).map(Number))

  if (selectedIds.has(normalizedId)) {
    selectedIds.delete(normalizedId)
  } else {
    selectedIds.add(normalizedId)
  }

  localFilters.bank_ids = Array.from(selectedIds)
}

function selectAllBanks() {
  localFilters.bank_ids = props.banks.map((bank) => Number(bank.id))
}

function clearBanks() {
  localFilters.bank_ids = []
}

function submit() {
  const payload = {
    ...localFilters,
    amount: localFilters.amount ? Number(localFilters.amount) : null,
    term_days: localFilters.term_days ? Number(localFilters.term_days) : null,
    bank_ids: Array.isArray(localFilters.bank_ids)
      ? localFilters.bank_ids.map(Number)
      : [],
    page: 1
  }

  banksDropdownOpen.value = false
  emit('update:modelValue', payload)
  emit('submit', payload)
}

function reset() {
  const payload = {
    amount: 50000,
    term_days: null,
    currency: 'RUB',
    bank_ids: [],
    capitalization_enabled: null,
    allow_topup: null,
    allow_partial_withdraw: null,
    auto_prolongation: null,
    page: 1,
    page_size: 12
  }

  banksDropdownOpen.value = false
  Object.assign(localFilters, payload)
  emit('update:modelValue', payload)
  emit('submit', payload)
}
</script>

<style scoped>
.filters {
  padding: 24px;
}

.filters h3 {
  margin: 0 0 18px;
}

.filters__grid {
  display: grid;
  gap: 14px;
}

.filters__field {
  display: grid;
  gap: 8px;
  position: relative;
}

.filters__label {
  font-size: 14px;
  color: var(--text-soft);
  font-weight: 700;
  letter-spacing: -0.01em;
}

.filters__hint {
  color: var(--text-soft);
  font-size: 14px;
}

.filters__hint--inside {
  padding: 10px 12px;
}

.filters__multiselect {
  position: relative;
}

.filters__multiselect-button {
  width: 100%;
  min-height: 46px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #fff;
  color: var(--text);
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.filters__multiselect-button:hover {
  border-color: #99d0ee;
  box-shadow: 0 0 0 4px rgba(153, 208, 238, 0.18);
}

.filters__multiselect-arrow {
  color: var(--text-soft);
  transition: transform 0.18s ease;
}

.filters__multiselect-arrow.is-open {
  transform: rotate(180deg);
}

.filters__multiselect-menu {
  position: absolute;
  z-index: 20;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  display: grid;
  gap: 8px;
  max-height: 260px;
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 18px 40px rgba(20, 43, 68, 0.16);
}

.filters__bank-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  color: var(--text);
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.filters__bank-option:hover {
  background: rgba(153, 208, 238, 0.16);
}

.filters__bank-option.is-selected {
  border-color: #99d0ee;
  background: rgba(153, 208, 238, 0.32);
  color: #102033;
}

.filters__bank-check {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 22px;
  border-radius: 999px;
  background: #eef7fc;
  color: #1277a8;
  font-size: 14px;
  font-weight: 900;
}

.filters__bank-option.is-selected .filters__bank-check {
  background: #99d0ee;
}

.filters__multiselect-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.filters__link-button,
.filters__ready-button {
  border: 0;
  border-radius: 999px;
  padding: 8px 12px;
  font: inherit;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.filters__link-button {
  background: #f4f8fb;
  color: var(--text);
}

.filters__ready-button {
  margin-left: auto;
  background: #99d0ee;
  color: #102033;
}

.filters__actions {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}
</style>
