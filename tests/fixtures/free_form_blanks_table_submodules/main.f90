program submodule_spellings
  use blank_parent, only: set_one, set_two
  implicit none
  integer :: first, second
  call set_one(first)
  if (first /= 7) stop 1
  call set_two(second)
  if (second /= 9) stop 2
  print '(A)', 'SUBMODULES'
end program
