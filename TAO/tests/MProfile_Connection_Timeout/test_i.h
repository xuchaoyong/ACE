
//=============================================================================
/**
 *  @file   test_i.h
 *
 *  $Id: test_i.h 93650 2011-03-28 08:44:53Z johnnyw $
 *
 *  @author Balachandran Natarajan <bala@isis-server.isis.vanderbilt.edu>
 */
//=============================================================================


#ifndef TAO_MPROFILE_CONNECTION_TIMEOUT_TEST_I_H
#define TAO_MPROFILE_CONNECTION_TIMEOUT_TEST_I_H

#include "testS.h"

/**
 * @class Simple_Server_i
 *
 * @brief Simpler Server implementation
 *
 * Implements the Simple_Server interface in test.idl
 */
class Simple_Server_i : public POA_Simple_Server
{
public:
  /// ctor
  Simple_Server_i (CORBA::ORB_ptr orb);

  /// ctor
  Simple_Server_i (void);

  // = The Simple_Server methods.
  CORBA::ULongLong remote_call (void);

  void shutdown (void);

private:
  CORBA::ORB_var orb_;

  CORBA::Long val_;

};

#endif /* TAO_MPROFILE_CONNECTION_TIMEOUT_TEST_I_H */
