#!/usr/bin/env python3

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(url='https://api.github.com/graphql')

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

# Provide a GraphQL query
query = gql('''
{
  search(query: "type:org", type: USER, first: 100) {
    userCount
    nodes {
      ... on Organization {
        name
        createdAt
        description
      }
    }
  }
}
''')

# Execute the query on the transport
result = client.execute(query)
print(result)
