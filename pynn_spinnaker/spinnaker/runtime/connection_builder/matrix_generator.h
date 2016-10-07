#pragma once

// Standard includes
#include <cstdint>

// Connection builder includes
#include "generator_factory.h"

// Forward declarations
namespace Common
{
  namespace Random
  {
    class MarsKiss64;
  }
}

// Namespaces
using namespace Common::Random;

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
// Forward declarations
namespace ConnectorGenerator
{
  class Base;
}

namespace ParamGenerator
{
  class Base;
}

namespace MatrixGenerator
{
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(uint32_t *matrixAddress, unsigned int maxRowSynapses,
    unsigned int weightFixedPoint, unsigned int numPostNeurons, unsigned int numRows,
    const ConnectorGenerator::Base *connectorGenerator,
    const ParamGenerator::Base *delayGenerator,
    const ParamGenerator::Base *weightGenerator,
    MarsKiss64 &rng) const = 0;

protected:
  //-----------------------------------------------------------------------------
  // Protected methods
  //-----------------------------------------------------------------------------
  void TraceUInt(uint32_t (&values)[1024], unsigned int number) const;
  void TraceInt(int32_t (&values)[1024], unsigned int number) const;
};

//-----------------------------------------------------------------------------
// Static
//-----------------------------------------------------------------------------
class Static : public Base
{
public:
  ADD_FACTORY_CREATOR(Static);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(uint32_t *matrixAddress, unsigned int maxRowSynapses,
    unsigned int weightFixedPoint, unsigned int numPostNeurons, unsigned int numRows,
    const ConnectorGenerator::Base *connectorGenerator,
    const ParamGenerator::Base *delayGenerator,
    const ParamGenerator::Base *weightGenerator,
    MarsKiss64 &rng) const;

private:
  Static(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t DelayBits = 3;
  static const uint32_t IndexBits = 10;
  static const uint32_t DelayMask = ((1 << DelayBits) - 1);
  static const uint32_t IndexMask = ((1 << IndexBits) - 1);
};

} // MatrixGenerator
} // ConnectionBuilder