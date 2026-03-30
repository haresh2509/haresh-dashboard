package com.haresh.expensetracker.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.haresh.expensetracker.data.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

class ExpenseViewModel(application: Application) : AndroidViewModel(application) {
    private val repository: ExpenseRepository
    val allExpenses: Flow<List<Expense>>
    val totalAmount: Flow<Double>

    init {
        val dao = AppDatabase.getDatabase(application).expenseDao()
        repository = ExpenseRepository(dao)
        allExpenses = repository.allExpenses
        totalAmount = allExpenses.map { list ->
            list.sumOf { it.amount }
        }
    }

    fun addExpense(amount: Double, category: String, date: Date, notes: String? = null) {
        viewModelScope.launch {
            val dateStr = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(date)
            val expense = Expense(amount = amount, category = category, date = dateStr, notes = notes)
            repository.insert(expense)
        }
    }

    fun updateExpense(expense: Expense) {
        viewModelScope.launch {
            repository.update(expense)
        }
    }

    fun deleteExpense(expense: Expense) {
        viewModelScope.launch {
            repository.delete(expense)
        }
    }

    fun getTotalForDate(date: Date): Flow<Double> = flow {
        val dateStr = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(date)
        emit(repository.getTotalForDate(dateStr))
    }

    fun getTotalForMonth(yearMonth: String): Flow<Double> = flow {
        emit(repository.getTotalForMonth(yearMonth))
    }
}
