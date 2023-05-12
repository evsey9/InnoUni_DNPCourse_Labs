import grpc
import calculator_pb2 as service
import calculator_pb2_grpc as stub
PORT = 50000


def main():
	with grpc.insecure_channel(f'localhost:{PORT}') as channel:
		stub_local = stub.CalculatorStub(channel)

		# Add
		add_request = service.Request(a=10, b=2)
		add_response = stub_local.Add(add_request)
		print(f"Add({add_request.a}, {add_request.b}) = {add_response.value}")

		# Subtract
		subtract_request = service.Request(a=10, b=2)
		subtract_response = stub_local.Subtract(subtract_request)
		print(f"Subtract({subtract_request.a}, {subtract_request.b}) = {subtract_response.value}")

		# Multiply
		multiply_request = service.Request(a=10, b=2)
		multiply_response = stub_local.Multiply(multiply_request)
		print(f"Multiply({multiply_request.a}, {multiply_request.b}) = {multiply_response.value}")

		# Divide
		divide_request = service.Request(a=10, b=2)
		divide_response = stub_local.Divide(divide_request)
		print(f"Divide({divide_request.a}, {divide_request.b}) = {divide_response.value}")

		# Divide by zero
		divide_zero_request = service.Request(a=10, b=0)
		divide_zero_response = stub_local.Divide(divide_zero_request)
		print(f"Divide({divide_zero_request.a}, {divide_zero_request.b}) = {divide_zero_response.value}")


if __name__ == '__main__':
	main()
