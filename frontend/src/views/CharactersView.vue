<template>
  <div class="characters-view">
    <CharacterManager />
  </div>
</template>

<script setup lang="ts">
import CharacterManager from '@/components/CharacterManager.vue'
</script>

<style scoped>
.characters-view {
  height: 100%;
  overflow: hidden;
}
</style>
