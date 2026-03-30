package com.haresh.expensetracker

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.haresh.expensetracker.data.Expense
import com.haresh.expensetracker.ui.theme.ExpenseTrackerTheme
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ExpenseTrackerTheme {
                Surface(color = MaterialTheme.colorScheme.background) {
                    MainScreen()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(viewModel: ExpenseViewModel = viewModel()) {
    val expenses by viewModel.allExpenses.collectAsState(initial = emptyList())
    val total by viewModel.totalAmount.collectAsState(initial = 0.0)
    var showAddDialog by remember { mutableStateOf(false) }
    var selectedDate by remember { mutableStateOf(Date()) }
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Expense Tracker", fontWeight = FontWeight.Bold) }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddDialog = true }
            ) {
                Icon(
                    painter = androidx.compose.ui.res.painterResource(id = android.R.drawable.ic_input_add),
                    contentDescription = "Add expense"
                )
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
        ) {
            // Summary
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Total Expenses", color = MaterialTheme.colorScheme.onPrimaryContainer)
                    Text(
                        "₹${String.format("%,.2f", total)}",
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Spacer(Modifier.height(8.dp))
                    Text("Date: ${dateFormat.format(selectedDate)}", fontSize = 12.sp)
                }
            }

            Spacer(Modifier.height(16.dp))

            // List
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(expenses) { expense ->
                    ExpenseRow(
                        expense = expense,
                        onDelete = { viewModel.deleteExpense(expense) }
                    )
                }
            }
        }
    }

    if (showAddDialog) {
        AddExpenseDialog(
            initialDate = selectedDate,
            onDismiss = { showAddDialog = false },
            onConfirm = { amount, category, date, notes ->
                viewModel.addExpense(amount, category, date, notes)
                showAddDialog = false
                selectedDate = date
            }
        )
    }
}

@Composable
fun ExpenseRow(expense: Expense, onDelete: () -> Unit) {
    val dateFormat = SimpleDateFormat("dd MMM", Locale.getDefault())
    Card(
        modifier = Modifier.fillMaxWidth(),
        onClick = onDelete
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(expense.category, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
                Text(
                    dateFormat.format(SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).parse(expense.date)),
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.secondary
                )
                if (!expense.notes.isNullOrBlank()) {
                    Text(expense.notes, fontSize = 12.sp, color = MaterialTheme.colorScheme.tertiary)
                }
            }
            Text(
                "-₹${String.format("%,.2f", expense.amount)}",
                color = MaterialTheme.colorScheme.error,
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddExpenseDialog(
    initialDate: Date,
    onDismiss: () -> Unit,
    onConfirm: (Double, String, Date, String?) -> Unit
) {
    var amount by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("") }
    var date by remember { mutableStateOf(initialDate) }
    var notes by remember { mutableStateOf("") }
    var showDatePicker by remember { mutableStateOf(false) }
    val dateFormat = SimpleDateFormat("dd MMM yyyy", Locale.getDefault())

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Expense") },
        text = {
            Column {
                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it.filter { c -> c.isDigit() || c == '.' } },
                    label = { Text("Amount (₹)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = category,
                    onValueChange = { category = it },
                    label = { Text("Category") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(8.dp))
                OutlinedButton(onClick = { showDatePicker = true }) {
                    Text("Date: ${dateFormat.format(date)}")
                }
                if (showDatePicker) {
                    val datePickerState = androidx.compose.material3.rememberDatePickerState(
                        initialSelectedDate = date.time
                    )
                    DatePicker(
                        state = datePickerState,
                        onDateChange = {
                            date = Date(it)
                            showDatePicker = false
                        }
                    )
                }
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Notes (optional)") },
                    maxLines = 2,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val amt = amount.toDoubleOrNull() ?: 0.0
                    if (amt <= 0 || category.isBlank()) return@Button
                    onConfirm(amt, category.trim(), date, notes.ifBlank { null })
                }
            ) {
                Text("Add")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
