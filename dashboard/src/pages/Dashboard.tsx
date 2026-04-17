import { Card, Metric, Text, Grid, Flex, Badge, Title } from '@tremor/react'

const Dashboard = () => {
  return (
    <div>
      <Title>Satoshi Pulse Dashboard</Title>
      <Grid numItems={1} numItemsSm={2} numItemsLg={3} className="mt-6 gap-6">
        <Card decoration="top" decorationColor="blue">
          <Text>Portfolio Value</Text>
          <Metric>$10,000.00</Metric>
        </Card>
        <Card decoration="top" decorationColor="green">
          <Text>P&L</Text>
          <Metric>$0.00</Metric>
        </Card>
        <Card decoration="top" decorationColor="amber">
          <Text>Active Signals</Text>
          <Metric>0</Metric>
        </Card>
      </Grid>
      <Grid numItems={1} numItemsSm={2} className="mt-6 gap-6">
        <Card>
          <Text>System Status</Text>
          <Flex justifyContent="between" className="mt-2">
            <Text>Collectors</Text>
            <Badge color="green">Running</Badge>
          </Flex>
          <Flex justifyContent="between">
            <Text>Database</Text>
            <Badge color="green">Connected</Badge>
          </Flex>
        </Card>
        <Card>
          <Text>Market Overview</Text>
          <Flex justifyContent="between" className="mt-2">
            <Text>BTC Price</Text>
            <Text>$0.00</Text>
          </Flex>
          <Flex justifyContent="between">
            <Text>Fear & Greed</Text>
            <Text>50</Text>
          </Flex>
        </Card>
      </Grid>
    </div>
  )
}

export default Dashboard