from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from flask import Flask, request, jsonify

import resolvers as r

PORT = 3002
HOST = '0.0.0.0'
app = Flask(__name__)

type_defs = load_schema_from_path("booking.graphql")
query = QueryType()
booking = ObjectType("Booking")
query.set_field('booking_with_id', r.booking_with_id)
mutation = MutationType()
mutation.set_field('update_booking_date', r.update_booking_date)
schema = make_executable_schema(type_defs, booking, query, mutation)

# root message
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>",200)

# graphql entry points
@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
                        schema,
                        data,
                        context_value=None,
                        debug=app.debug
                    )
    status_code = 200 if success else 400
    return jsonify(result), status_code

if __name__ == "__main__":
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)