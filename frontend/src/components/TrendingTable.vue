<template>
	<div class="trending-table">
		<table>
			<thead>
				<tr>
					<th rowspan="2">年份</th>
					<th v-for="month in months" :key="month">{{ month }}</th>
				</tr>
			</thead>
			<tbody>
				<template v-for="year in years" :key="year">
					<tr>
						<td>{{ year }}</td>
						<template v-for="(value, monthIndex) in getYearData(year)" :key="year + '-month-' + monthIndex">
							<td>{{ valueDisplay(value) }}</td>
						</template>
					</tr>
				</template>
			</tbody>
		</table>
	</div>
</template>

<script setup>
/* eslint-env vue/setup-compiler-macros */
import { ref, computed, watch, onMounted } from 'vue';

const props = defineProps({
	data: { type: Object, required: true }
});

const yearData = ref({});

// computed
const months = computed(() => ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']);

const years = computed(() => {
	const startYear = new Date(props.data.時間起點).getFullYear();
	const endYear = new Date(props.data.時間終點).getFullYear();
	const arr = [];
	for (let y = startYear; y <= endYear; y++) arr.push(y);
	return arr;
});

function getYearData(year) {
	return yearData.value[year];
}

function processInitData() {
	const start = new Date(props.data.時間起點);
	const end = new Date(props.data.時間終點);

	const startMonth = start.getMonth() + 1;
	const endMonth = end.getMonth() + 1;
	const startYear = start.getFullYear();
	const endYear = end.getFullYear();

	const stats = String(props.data.統計值 ?? '').split(',');

	const ymap = {};
	for(let year = startYear; year <= endYear; year++) {
		const yearPrices = [];
		for(let month = 1; month <= 12; month++) {
			if(year === startYear && month < startMonth) {
				yearPrices.push('0');
			}
			else if(year === endYear && month > endMonth) {
				yearPrices.push('0');
			}
			else {
				yearPrices.push(stats[month + (year - startYear) * 12 - startMonth]);
			}
		}
		ymap[year] = yearPrices;
	}
	yearData.value = ymap;
}

function valueDisplay(value) {
	return value === '0' ? '-' : value;
}

onMounted(() => {
	processInitData();
});

watch(
	() => props.data,
	(newVal) => { if(newVal) processInitData(); },
	{ deep: true },
);

</script>

<style scoped>
.trending-table {
	margin-top: 2em;
}

table {
	width: 100%;
	border-collapse: collapse;
}

th,
td {
	border: 1px solid #ccc;
	padding: 0.5em;
	text-align: center;
}
</style>