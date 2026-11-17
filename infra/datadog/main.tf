terraform {
  required_version = ">= 1.6"
  required_providers {
    datadog = {
      source  = "DataDog/datadog"
      version = "~> 3.0"
    }
  }
}

provider "datadog" {}

resource "datadog_dashboard" "api" {
  title       = "Portfolio API"
  description = "HTTP traffic and Kubernetes resource usage for the portfolio API."
  layout_type = "ordered"

  widget {
    timeseries_definition {
      title = "HTTP requests by status class"
      request {
        q = "sum:portfolio.requests.count{env:portfolio,service:portfolio-api} by {status_class}.as_count()"
      }
    }
  }

  widget {
    timeseries_definition {
      title = "HTTP 5xx error rate (%)"
      request {
        formula {
          formula_expression = "100 * a / b"
          alias              = "5xx error rate (%)"
        }
        query {
          metric_query {
            data_source = "metrics"
            name        = "a"
            query       = "sum:portfolio.requests.count{env:portfolio,service:portfolio-api,status_class:5xx}.as_count()"
            aggregator  = "sum"
          }
        }
        query {
          metric_query {
            data_source = "metrics"
            name        = "b"
            query       = "sum:portfolio.requests.count{env:portfolio,service:portfolio-api}.as_count()"
            aggregator  = "sum"
          }
        }
      }
    }
  }

  widget {
    timeseries_definition {
      title = "API container CPU usage"
      request {
        q = "sum:container.cpu.usage{kube_namespace:portfolio,container_name:api}"
      }
    }
  }

  widget {
    timeseries_definition {
      title = "API container memory usage"
      request {
        q = "sum:container.memory.usage{kube_namespace:portfolio,container_name:api}"
      }
    }
  }
}

resource "datadog_monitor" "errors" {
  name                = "Portfolio API elevated HTTP 5xx count"
  type                = "metric alert"
  query               = "sum(last_5m):sum:portfolio.requests.count{env:portfolio,service:portfolio-api,status_class:5xx}.as_count() > 5"
  message             = "Check the Portfolio API dashboard and logs using service:portfolio-api env:portfolio. Then inspect the Argo CD revision and Kubernetes pod status."
  require_full_window = false
  notify_no_data      = false
  monitor_thresholds {
    critical = 5
  }
  tags = ["service:portfolio-api", "env:portfolio"]
}
