package com.example.drivepdfmaster

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.drivepdfmaster.databinding.ActivityMainBinding
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val client = OkHttpClient()
    
    // Change this to your computer's IP address (e.g., http://192.168.1.5:5000)
    // 10.0.2.2 is used for Android Emulator to access host machine localhost
    private val baseUrl = "http://192.168.56.1:5000"
    
    private var jobId: String? = null
    private var downloadFilename: String? = null
    private val handler = Handler(Looper.getMainLooper())
    private var isPolling = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnExtract.setOnClickListener {
            startExtraction()
        }

        binding.btnDownload.setOnClickListener {
            downloadPdf()
        }
    }

    private fun startExtraction() {
        val url = binding.urlInput.text.toString().trim()
        if (url.isEmpty()) {
            Toast.makeText(this, "Please enter a URL", Toast.LENGTH_SHORT).show()
            return
        }

        binding.btnExtract.isEnabled = false
        binding.statusLayout.visibility = View.VISIBLE
        binding.btnDownload.visibility = View.GONE
        binding.progressBar.progress = 5
        binding.statusText.text = "Connecting to server..."

        val formBody = FormBody.Builder()
            .add("url", url)
            .build()

        val request = Request.Builder()
            .url("$baseUrl/extract")
            .post(formBody)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread { resetUI("Connection failed: ${e.message}") }
            }

            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string()
                if (response.isSuccessful && body != null) {
                    val json = JSONObject(body)
                    jobId = json.getString("job_id")
                    runOnUiThread { 
                        isPolling = true
                        pollStatus() 
                    }
                } else {
                    runOnUiThread { resetUI("Error: ${response.message}") }
                }
            }
        })
    }

    private fun pollStatus() {
        if (!isPolling || jobId == null) return

        val request = Request.Builder()
            .url("$baseUrl/status/$jobId")
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread { resetUI("Poll failed: ${e.message}") }
            }

            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string()
                if (response.isSuccessful && body != null) {
                    val json = JSONObject(body)
                    val status = json.getString("status")
                    val progress = json.getInt("progress")

                    runOnUiThread {
                        binding.progressBar.progress = progress
                        binding.statusText.text = status

                        if (status == "Completed") {
                            isPolling = false
                            downloadFilename = json.getString("file")
                            binding.btnExtract.isEnabled = true
                            binding.btnDownload.visibility = View.VISIBLE
                        } else if (status.startsWith("Error")) {
                            isPolling = false
                            resetUI(status)
                        } else {
                            handler.postDelayed({ pollStatus() }, 1500)
                        }
                    }
                }
            }
        })
    }

    private fun downloadPdf() {
        if (downloadFilename == null) return

        val downloadUrl = "$baseUrl/download/$downloadFilename"
        val request = DownloadManager.Request(Uri.parse(downloadUrl))
            .setTitle("DrivePDF: $downloadFilename")
            .setDescription("Downloading extracted PDF")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, downloadFilename)
            .setAllowedOverMetered(true)
            .setAllowedOverRoaming(true)

        val downloadManager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        downloadManager.enqueue(request)
        
        Toast.makeText(this, "Download started. Check notifications.", Toast.LENGTH_LONG).show()
    }

    private fun resetUI(message: String) {
        binding.btnExtract.isEnabled = true
        binding.statusText.text = message
        binding.progressBar.progress = 0
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }
}
