import grpc
import math
import calculator_pb2 as stub
import calculator_pb2_grpc as service
from concurrent.futures import ThreadPoolExecutor
PORT = 50000


class Calculator(service.CalculatorServicer):
	def Add(self, request, context):
		print(f"Add({request.a},{request.b})")
		result = request.a + request.b
		return stub.Response(value=result)

	def Subtract(self, request, context):
		print(f"Subtract({request.a},{request.b})")
		result = request.a - request.b
		return stub.Response(value=result)

	def Multiply(self, request, context):
		print(f"Multiply({request.a},{request.b})")
		result = request.a * request.b
		return stub.Response(value=result)

	def Divide(self, request, context):
		print(f"Divide({request.a},{request.b})")
		if request.b == 0:
			result = math.nan
		else:
			result = request.a / request.b
		return stub.Response(value=result)


def main():
	server = grpc.server(ThreadPoolExecutor(max_workers=10))
	service.add_CalculatorServicer_to_server(Calculator(), server)
	server.add_insecure_port(f'[::]:{PORT}')
	server.start()
	print(f"gRPC server is listening on 0.0.0.0:{PORT}")
	try:
		server.wait_for_termination()
	except KeyboardInterrupt:
		print("Shutting down...")


if __name__ == '__main__':
	main()
