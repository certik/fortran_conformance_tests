! rule: S7.5.10-001
! covers: parameter-specifier-source-use
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
module sc_b_pdt_mod
implicit none
type :: packet(k)
  integer, kind :: k=kind(0.0)
  real(kind=k) :: payload
end type packet
contains
subroutine observe(x)
  type(packet(kind(0.0))), intent(in) :: x
  integer :: checks
  checks = 0
  if (kind(x%payload) /= kind(0.0)) error stop 1
  checks = checks + 1
  if (x%payload /= 4.0) error stop 2
  checks = checks + 1
  if (checks /= 2) error stop 3
end subroutine observe
end module sc_b_pdt_mod
program structure_constructor_7_5_10_b_pdt_kind_parameter
use sc_b_pdt_mod
implicit none
call observe(packet(k=kind(0.0))(payload=4.0))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR PDT KIND PARAMETER OK'
end program structure_constructor_7_5_10_b_pdt_kind_parameter
