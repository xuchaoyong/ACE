//
// $Id: simple_test_i.cpp 97041 2013-04-18 07:28:52Z mcorino $
//

#include "simple_test_i.h"

Simple_Test_i::Simple_Test_i (CORBA::ORB_ptr orb)
  : orb_ (CORBA::ORB::_duplicate (orb))
{
}

void
Simple_Test_i::shutdown (void)
{
  this->orb_->shutdown (0);
}