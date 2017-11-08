#!/usr/bin/env ruby

require_relative 'anagram_client'
require 'zlib'
require "benchmark"
require 'benchmark/bigo'


FILENAME = 'dictionary.txt.gz'
SLICE_SIZE = 100


def data(filename)
	#puts("Creating array...")
	Zlib::GzipReader.open(filename) do |gz|
		gz.read.split("\n")
	end
end

def post_dictionary(array)
	#puts("Posting data to API...")

	@client = AnagramClient.new(ARGV)

	array.each_slice(SLICE_SIZE) do |slice|
		@client.post('/words.json', nil, {"words" => slice }) rescue nil
	end
end

def delete_all()
	@client = AnagramClient.new(ARGV)
	@client.delete('/words.json') rescue nil
end

# Post Benchmarking
puts("N\tTime")
run_data = []
i = 10
while i <= 1_000
	j = i
	limit = j * 10
	while j <= limit
		data = data(FILENAME)
		row_data = []
		delete_all()
		data = data.sample(j)
		time = Benchmark.realtime do
			post_dictionary(data)
		end
		run_data.push([j, time])
		puts("#{j}\t#{time}")
		j = j * 2
	end
	i = i * 10
end

file_content = ""
run_data.each_with_index do |x, xi|
	x.each_with_index do |y, yi|
		file_content = file_content + "#{y}" + ", "
	end
	file_content = file_content.chomp(", ")
	file_content = file_content + "\n"
end

File.write('benchmark_post.csv', file_content)


###################################
# Attempt at using benchmark/bigo
###################################

# Benchmark.bigo do |x|
#   x.generator do |size|
#     data(FILENAME).sample(size)
#   end

#   x.min_size = 10000
#   x.step_size = 10000

#   x.report('POST /words.json') do |array, size|
#     post_dictionary(array)
#   end

#   x.chart! 'chart_anagram_post.html'

#   x.compare!
# end

# Calculating -------------------------------------
# POST /words.json 10000
# /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-bigo-1.0.0/lib/benchmark/bigo/report.rb:14:in `add_entry': wrong number of arguments (given 5, expected 6) (ArgumentError)
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-ips-2.7.2/lib/benchmark/ips/job.rb:345:in `create_report'
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-ips-2.7.2/lib/benchmark/ips/job.rb:283:in `block in run_benchmark'
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-ips-2.7.2/lib/benchmark/ips/job.rb:239:in `each'
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-ips-2.7.2/lib/benchmark/ips/job.rb:239:in `run_benchmark'
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-ips-2.7.2/lib/benchmark/ips/job.rb:193:in `block in run'
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-ips-2.7.2/lib/benchmark/ips/job.rb:192:in `times'
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-ips-2.7.2/lib/benchmark/ips/job.rb:192:in `run'
#         from /home/kruser/.rbenv/versions/2.4.2/lib/ruby/gems/2.4.0/gems/benchmark-bigo-1.0.0/lib/benchmark/bigo.rb:37:in `bigo'
#         from anagram_benchmark.rb:52:in `<main>'

