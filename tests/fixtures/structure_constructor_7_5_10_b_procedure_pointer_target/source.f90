! rule: S7.5.10-007
! covers: procedure-target-call
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
module sc_b_procptr_mod
implicit none
abstract interface
  integer function fun(i)
    integer, intent(in) :: i
  end function fun
end interface
type :: holder
  procedure(fun), pointer, nopass :: action => null()
end type holder
contains
integer function worker(i)
  integer, intent(in) :: i
  worker = i + 5
end function worker
integer function other_worker(i)
  integer, intent(in) :: i
  other_worker = i + 6
end function other_worker
subroutine observe(x)
  type(holder), intent(in) :: x
  if (.not. associated(x%action)) error stop 1
  if (x%action(3) /= 8) error stop 2
end subroutine observe
end module sc_b_procptr_mod
program structure_constructor_7_5_10_b_procptr
use sc_b_procptr_mod
implicit none
call observe(holder(worker))
write(*,'(a)') 'STRUCTURE CONSTRUCTOR PROCEDURE POINTER TARGET OK'
end program structure_constructor_7_5_10_b_procptr
