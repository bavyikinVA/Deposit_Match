<template>
  <section class="container catalog-page">
    <div class="catalog-page__head">
      <div>
        <h1 class="section-title">Каталог вкладов</h1>
        <p class="section-subtitle">Подбор вкладов по ключевым условиям.</p>
      </div>

      <div class="catalog-page__summary card">
        <div>Найдено предложений: <strong>{{ store.total }}</strong></div>
        <!--<div v-if="store.items.length">Показано: <strong>{{ store.items.length }}</strong></div>-->
      </div>
    </div>

    <div class="catalog-page__layout">
      <FiltersPanel
        v-model="filters"
        :banks="store.banks"
        :banks-loading="store.banksLoading"
        @submit="handleSubmit"
      />

      <div class="catalog-page__content">
        <UiLoader v-if="store.loading" />
        <div v-else-if="store.error" class="catalog-page__error card">{{ store.error }}</div>
        <UiEmptyState v-else-if="!store.items.length" />
        <template v-else>
          <DepositGrid :items="store.items" />

          <div v-if="store.hasMore" class="catalog-page__more">
            <button
              class="btn btn-primary catalog-page__more-button"
              type="button"
              :disabled="store.loadingMore"
              @click="loadMore"
            >
              {{ store.loadingMore ? 'Загрузка...' : 'Показать ещё' }}
            </button>
          </div>

          <div v-else class="catalog-page__end">
            Все найденные предложения загружены
          </div>
        </template>
      </div>
    </div>

    <BackToTopButton />
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import BackToTopButton from '../components/BackToTopButton.vue'
import DepositGrid from '../components/DepositGrid.vue'
import FiltersPanel from '../components/FiltersPanel.vue'
import UiEmptyState from '../components/UiEmptyState.vue'
import UiLoader from '../components/UiLoader.vue'
import { useDepositsStore } from '../stores/deposits'

const store = useDepositsStore()
const filters = ref({ ...store.filters })

async function handleSubmit(payload) {
  await store.loadDeposits({ ...payload, page: 1 })
  filters.value = { ...store.filters }
}

async function loadMore() {
  await store.loadMore()
  filters.value = { ...store.filters }
}

onMounted(async () => {
  await Promise.all([
    store.loadBanks(),
    store.loadDeposits()
  ])

  filters.value = { ...store.filters }
})
</script>

<style scoped>
.catalog-page {
  padding: 28px 0 44px;
}

.catalog-page__head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-end;
  margin-bottom: 22px;
}

.catalog-page__summary {
  padding: 18px 22px;
  display: grid;
  gap: 6px;
}

.catalog-page__layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
}

.catalog-page__content {
  min-width: 0;
}

.catalog-page__error {
  padding: 24px;
  color: #b42318;
}

.catalog-page__more {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

.catalog-page__more-button {
  min-width: 190px;
}

.catalog-page__end {
  margin-top: 24px;
  text-align: center;
  color: var(--text-soft);
  font-weight: 600;
}

@media (max-width: 980px) {
  .catalog-page__layout {
    grid-template-columns: 1fr;
  }

  .catalog-page__head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
