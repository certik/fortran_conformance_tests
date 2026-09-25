! rule: C7108
! covers: resolvable-function-precedence, keyword-constructor-fallback, type-constructor-fallback
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
module sc_b_generic_mod
implicit none
type :: record
  integer :: payload
end type record
type :: token
  integer :: payload
end type token
interface record
  module procedure make_record
end interface record
interface token
  module procedure make_token
end interface token
contains
function make_record(n) result(out)
  integer, intent(in) :: n
  type(record) :: out
  out%payload = n + 18
end function make_record
function make_token(s) result(out)
  character(*), intent(in) :: s
  type(token) :: out
  out%payload = len(s) + 40
end function make_token
subroutine observe()
  type(record) :: generic_value
  type(record) :: keyword_value
  type(token) :: fallback_value
  generic_value = record(11)
  keyword_value = record(payload=11)
  fallback_value = token(21)
  if (generic_value%payload /= 29) error stop 1
  if (keyword_value%payload /= 11) error stop 2
  if (fallback_value%payload /= 21) error stop 3
end subroutine observe
end module sc_b_generic_mod
program structure_constructor_7_5_10_b_generic_precedence
use sc_b_generic_mod
implicit none
call observe()
write(*,'(a)') 'STRUCTURE CONSTRUCTOR GENERIC PRECEDENCE OK'
end program structure_constructor_7_5_10_b_generic_precedence
