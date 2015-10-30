#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../../common/log.h"

//-----------------------------------------------------------------------------
// SynapseProcessor::SynapseTypes::Static
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
namespace SynapseTypes
{
template<typename T, typename W, unsigned int D, unsigned int I>
class Static
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  // One word for a synapse-count and 1024 synapses
  static const unsigned int MaxRowWords = 1025;
    
  //-----------------------------------------------------------------------------
  // Public static methods
  //-----------------------------------------------------------------------------
  template<typename F>
  static bool ProcessRow(uint tick, uint32_t (&dmaBuffer)[MaxRowWords],
                         F applyInputFunction)
  {
    register T *synapticWords = (T*)&dmaBuffer[1];
    register uint32_t count = dmaBuffer[0];
    
    LOG_PRINT(LOG_LEVEL_TRACE, "Processing row with %u synapses", count);
    
    for(; count > 0; count--)
    {
      // Get the next 32 bit word from the synaptic_row
      // (should autoincrement pointer in single instruction)
      T synapticWord = *synapticWords++;

      // Add weight to ring-buffer
      applyInputFunction(GetDelay(synapticWord) + tick, 
        GetIndex(synapticWord), GetWeight(synapticWord));
    }
    
    return true;
  }
  
  static unsigned int GetRowWords(unsigned int rowSynapses)
  {
    // One header word and a synapse
    return 1 + ((rowSynapses * sizeof(T)) / 4);
  }

private:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const T DelayMask = ((1 << D) - 1);
  static const T IndexMask = ((1 << I) - 1);
  
  //-----------------------------------------------------------------------------
  // Private static methods
  //-----------------------------------------------------------------------------
   static T GetIndex(T word){ return (word & IndexMask); }
   static T GetDelay(T word){ return ((word >> I) & DelayMask); }
   static W GetWeight(T word){ return (W)(word >> (8 * (sizeof(T) - sizeof(W)))); }
};
} // SynapseTypes
} // SynapseProcessor