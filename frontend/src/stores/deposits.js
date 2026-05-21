import { defineStore } from 'pinia'
import {
    fetchDeposits,
    calculateDeposit,
    fetchDepositsStats,
    fetchDepositVariantById,
    getDepositBanks
} from '../api/deposits'

export const useDepositsStore = defineStore('deposits', {
    state: () => ({
        items: [],
        total: 0,
        page: 1,
        pageSize: 12,
        loading: false,
        loadingMore: false,
        error: '',

        banks: [],
        banksLoading: false,
        banksError: '',

        calculatorLoading: false,
        calculatorError: '',
        calculationResult: null,

        selectedVariant: null,
        selectedVariantLoading: false,
        selectedVariantError: '',

        statsLoading: false,
        statsError: '',
        stats: {
            totalOffers: 0,
            totalBanks: 0,
            topupOffers: 0,
            capitalizationOffers: 0
        },

        filters: {
            amount: 50000,
            // Срок по умолчанию не задаём: каталог не должен отсеивать вклады
            // из-за условных 367/365/360 дней до выбора пользователя.
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
    }),

    getters: {
        hasMore: (state) => state.items.length < state.total
    },

    actions: {
        cleanParams(params) {
            const result = { ...params }

            Object.keys(result).forEach((key) => {
                const value = result[key]

                if (
                    value === null ||
                    value === '' ||
                    value === undefined ||
                    (Array.isArray(value) && value.length === 0)
                ) {
                    delete result[key]
                }
            })

            return result
        },

        async loadBanks() {
            this.banksLoading = true
            this.banksError = ''

            try {
                this.banks = await getDepositBanks()
            } catch (error) {
                this.banksError = error?.response?.data?.detail || 'Не удалось загрузить банки'
            } finally {
                this.banksLoading = false
            }
        },

        async loadDeposits(override = {}, options = {}) {
            const append = Boolean(options.append)

            if (append) {
                this.loadingMore = true
            } else {
                this.loading = true
            }

            this.error = ''

            try {
                const params = this.cleanParams({
                    ...this.filters,
                    ...override
                })

                const data = await fetchDeposits(params)
                const items = data.items || []

                this.items = append ? [...this.items, ...items] : items
                this.total = data.total || 0
                this.page = data.page || 1
                this.pageSize = data.page_size || 12

                this.filters = {
                    ...this.filters,
                    ...override,
                    page: this.page,
                    page_size: this.pageSize
                }
            } catch (error) {
                this.error = error?.response?.data?.detail || 'Не удалось загрузить предложения'
            } finally {
                this.loading = false
                this.loadingMore = false
            }
        },

        async loadMore() {
            if (this.loadingMore || this.loading || !this.hasMore) {
                return
            }

            await this.loadDeposits(
                {
                    page: this.page + 1,
                    page_size: this.pageSize
                },
                {
                    append: true
                }
            )
        },

        async loadStats() {
            this.statsLoading = true
            this.statsError = ''

            try {
                const data = await fetchDepositsStats()

                this.stats = {
                    totalOffers: Number(data.total_offers || 0),
                    totalBanks: Number(data.total_banks || 0),
                    topupOffers: Number(data.topup_offers || 0),
                    capitalizationOffers: Number(data.capitalization_offers || 0)
                }
            } catch (error) {
                this.statsError = error?.response?.data?.detail || 'Не удалось загрузить статистику'
            } finally {
                this.statsLoading = false
            }
        },

        setSelectedVariant(variant) {
            this.selectedVariant = variant
        },

        async loadVariantById(variantId) {
            if (!variantId) return

            const hasFullSelectedVariant =
                this.selectedVariant &&
                Number(this.selectedVariant.id) === Number(variantId) &&
                Array.isArray(this.selectedVariant.base_rates) &&
                this.selectedVariant.base_rates.length > 0

            // Карточка из каталога содержит краткую модель без base_rates.
            // Для калькулятора всегда нужна полная карточка с /api/deposits/{id}.
            if (hasFullSelectedVariant) {
                return
            }

            this.selectedVariantLoading = true
            this.selectedVariantError = ''

            try {
                const data = await fetchDepositVariantById(variantId)
                this.selectedVariant = data
            } catch (error) {
                this.selectedVariantError = error?.response?.data?.detail || 'Не удалось загрузить вклад'
            } finally {
                this.selectedVariantLoading = false
            }
        },

        async goToPage(page) {
            await this.loadDeposits({ page })
        },

        async runCalculation(payload) {
            this.calculatorLoading = true
            this.calculatorError = ''
            this.calculationResult = null

            try {
                this.calculationResult = await calculateDeposit(payload)
            } catch (error) {
                this.calculatorError = error?.response?.data?.detail || 'Не удалось выполнить расчёт'
            } finally {
                this.calculatorLoading = false
            }
        }
    }
})
