import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class IPOAdapter(private val ipoList: List<IPO>) : RecyclerView.Adapter<IPOAdapter.IPOViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): IPOViewHolder {
        val itemView = LayoutInflater.from(parent.context).inflate(R.layout.ipo_item, parent, false)
        return IPOViewHolder(itemView)
    }

    override fun onBindViewHolder(holder: IPOViewHolder, position: Int) {
        val currentIPO = ipoList[position]
        holder.companyName.text = currentIPO.companyName
        holder.industry.text = currentIPO.industry
        holder.priceRange.text = currentIPO.priceRange
    }

    override fun getItemCount() = ipoList.size

    class IPOViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val companyName: TextView = itemView.findViewById(R.id.companyName)
        val industry: TextView = itemView.findViewById(R.id.industry)
        val priceRange: TextView = itemView.findViewById(R.id.priceRange)
    }
}
