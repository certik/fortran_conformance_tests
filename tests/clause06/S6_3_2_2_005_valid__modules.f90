! rule: S6.3.2.2-005
! covers: end-module
! evidence: positive-control
module compact_module
  implicit none
  integer, parameter :: first = 7
endmodule compact_module

module spaced_module
  implicit none
  integer, parameter :: second = 9
end module spaced_module

program module_spellings
  use compact_module, only: first
  use spaced_module, only: second
  implicit none
  if (first /= 7) stop 1
  if (second /= 9) stop 2
end program
