#ifndef Echo__h_
#define Echo__h_
/**
 * @file Echo.h
 *
 * $Id: Echo.h 77008 2007-02-12 11:52:38Z johnnyw $
 *
 * @author Carlos O'Ryan <coryan@atdesk.com>
 *
 */
#include "TestS.h"

class Echo : public POA_Test::Echo
{
public:
  Echo(CORBA::ORB_ptr orb);

  virtual Test::Payload * echo_payload (Test::Payload const & data);

private:
  CORBA::ORB_var orb_;
};

#endif /* Echo__h_ */
