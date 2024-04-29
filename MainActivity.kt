import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val ipoList = listOf(
            IPO("Company A", "Tech", "500-600"),
            IPO("Company B", "Finance", "800-900"),
            IPO("Company C", "Healthcare", "200-300")
        )

        val recyclerView: RecyclerView = findViewById(R.id.recyclerView)
        recyclerView.adapter = IPOAdapter(ipoList)
        recyclerView.layoutManager = LinearLayoutManager(this)
    }
}
