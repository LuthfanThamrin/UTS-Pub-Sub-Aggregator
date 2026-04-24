# BAB 1
Sistem terdistribusi merupakan kumpulan komputer yang saling terhubung dan bekerja sama untuk menyediakan layanan secara terpadu, dengan karakteristik utama seperti resource sharing, scalability, dependability, dan distribution transparency. Dalam konteks Pub-Sub log aggregator, karakteristik ini terlihat pada kemampuan sistem mengumpulkan log dari banyak sumber secara transparan tanpa pengguna mengetahui lokasi sebenarnya. Namun, desain ini membawa trade-off, terutama antara konsistensi dan performa. Untuk mencapai skalabilitas tinggi, sistem sering mengorbankan konsistensi kuat dan menggunakan pendekatan eventual consistency. Selain itu, kompleksitas meningkat karena adanya partial failures, di mana sebagian komponen dapat gagal tanpa menghentikan keseluruhan sistem. Dengan demikian, Pub-Sub memberikan fleksibilitas dan skalabilitas tinggi, tetapi dengan biaya kompleksitas dan potensi inkonsistensi sementara.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 7–8, 10–24.)*

---

# BAB 2
Arsitektur client-server merupakan model komunikasi langsung antara klien dan server, sedangkan publish-subscribe menggunakan perantara (broker) untuk mendistribusikan pesan berdasarkan topik. Pada client-server, hubungan bersifat tightly coupled, sehingga kurang fleksibel dalam skala besar. Sebaliknya, Pub-Sub bersifat loosely coupled, memungkinkan produsen dan konsumen tidak saling mengetahui satu sama lain. Hal ini meningkatkan skalabilitas dan fleksibilitas sistem. Pub-Sub lebih tepat digunakan pada sistem log aggregator karena sifatnya yang event-driven dan kebutuhan untuk menangani banyak sumber data secara paralel. Secara teknis, Pub-Sub mendukung distribusi beban yang lebih baik dan meminimalkan bottleneck dibandingkan client-server.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 68.)*

---

# BAB 3
Dalam komunikasi terdistribusi, terdapat beberapa model delivery semantics, yaitu at-least-once dan exactly-once. Model at-least-once menjamin pesan sampai, tetapi memungkinkan duplikasi, sedangkan exactly-once menjamin tidak ada duplikasi namun lebih kompleks dan mahal untuk diimplementasikan. Karena sistem terdistribusi sering mengalami retry akibat kegagalan jaringan atau node, maka konsep idempotent consumer menjadi penting. Idempotency memastikan bahwa pemrosesan ulang pesan yang sama tidak mengubah hasil akhir. Hal ini krusial dalam log aggregator untuk mencegah data ganda dan menjaga integritas sistem meskipun terjadi pengiriman ulang.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 220.)*

---

# BAB 4
Penamaan dalam sistem terdistribusi harus unik dan konsisten untuk mendukung identifikasi dan akses sumber daya. Dalam Pub-Sub, topic biasanya menggunakan struktur hierarkis seperti `logs.service.environment.region` untuk memudahkan pengelompokan dan routing pesan. Sementara itu, event_id harus bersifat unik dan tahan terhadap collision, misalnya menggunakan UUID atau hash. Skema penamaan ini sangat berpengaruh terhadap proses deduplikasi, karena sistem dapat mengidentifikasi pesan yang sama berdasarkan event_id. Dengan desain yang baik, proses deduplication menjadi lebih efisien dan akurat.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 326.)*

---

# BAB 5
Ordering dalam sistem terdistribusi berkaitan dengan urutan kejadian yang diproses oleh sistem. Namun, total ordering tidak selalu diperlukan, terutama pada sistem seperti log aggregator yang lebih fokus pada throughput daripada urutan absolut. Pendekatan praktis yang digunakan adalah kombinasi timestamp dan monotonic counter untuk menjaga urutan lokal. Selain itu, konsep logical clock seperti Lamport clock digunakan untuk menentukan hubungan kausal antar event. Keterbatasannya adalah adanya kemungkinan clock drift dan ketidaksesuaian waktu antar node, sehingga urutan global tidak selalu akurat.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 260.)*

---

# BAB 6
Sistem terdistribusi rentan terhadap berbagai jenis kegagalan seperti duplikasi pesan, out-of-order delivery, dan kegagalan node. Kegagalan ini sering bersifat parsial dan sulit dideteksi secara langsung. Untuk mengatasi hal tersebut, digunakan strategi seperti retry dengan backoff, penyimpanan persisten (durable storage), serta deduplication store. Selain itu, replikasi data juga digunakan untuk meningkatkan ketersediaan dan toleransi terhadap kegagalan. Pendekatan ini memungkinkan sistem tetap berjalan meskipun terjadi gangguan pada sebagian komponen.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 463–466.)*

---

# BAB 7
Eventual consistency adalah model konsistensi di mana sistem akan mencapai keadaan konsisten setelah periode tertentu tanpa adanya update baru. Dalam log aggregator, hal ini berarti data log mungkin tidak langsung sinkron di semua node, tetapi akan menjadi konsisten seiring waktu. Kombinasi antara idempotency dan deduplication membantu memastikan bahwa meskipun terjadi pengiriman ulang atau keterlambatan, hasil akhir tetap benar. Model ini dipilih karena memberikan keseimbangan antara performa dan konsistensi dalam sistem berskala besar.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 406.)*

---

# BAB 8
Evaluasi sistem terdistribusi dilakukan dengan mengukur beberapa metrik utama seperti throughput, latency, dan duplicate rate. Throughput mengukur jumlah pesan yang dapat diproses per detik, sedangkan latency mengukur waktu yang dibutuhkan dari pengiriman hingga pemrosesan pesan. Duplicate rate menunjukkan tingkat duplikasi pesan yang terjadi akibat retry. Metrik ini berkaitan langsung dengan keputusan desain, seperti pemilihan delivery semantics dan strategi konsistensi. Misalnya, penggunaan at-least-once meningkatkan throughput tetapi juga meningkatkan duplicate rate. Oleh karena itu, desain sistem harus mempertimbangkan trade-off antara performa, konsistensi, dan keandalan.  
*(Tanenbaum, A. S., & van Steen, M., Distributed Systems, 4th Edition, 2023, hlm. 462–466.)*

---

# DAFTAR PUSTAKA
Tanenbaum, A. S., & van Steen, M. (2023). *Distributed Systems* (4th ed., Version 4.01). Maarten van Steen.