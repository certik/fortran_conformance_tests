module i169c_assoc_host_mod
  implicit none
  abstract interface
    integer function int_fun(x)
      integer, intent(in) :: x
    end function int_fun
  end interface
contains
  recursive subroutine host(depth, carried, saw)
    integer, intent(in) :: depth
    procedure(int_fun), pointer :: carried
    logical, intent(inout) :: saw(6)
    procedure(int_fun), pointer :: current, current2
    current => inner
    if (depth == 1) then
      carried => inner
      call host(2, carried, saw)
    else
      current2 => inner
      saw(1) = associated(current, inner)
      saw(2) = .not. associated(carried, inner)
      saw(3) = .not. associated(carried, current)
      saw(4) = associated(current, current2)
      call dummy_check(inner, current, carried, saw)
    end if
  contains
    integer function inner(x)
      integer, intent(in) :: x
      inner = x + depth
    end function inner
    subroutine dummy_check(dummy, pcur, pother, saw)
      procedure(int_fun) :: dummy
      procedure(int_fun), pointer :: pcur, pother
      logical, intent(inout) :: saw(6)
      saw(5) = associated(pcur, dummy)
      saw(6) = .not. associated(pother, dummy)
    end subroutine dummy_check
  end subroutine host
end module i169c_assoc_host_mod
program i169c_associated_host_instance
  use i169c_assoc_host_mod
  implicit none
  procedure(int_fun), pointer :: outer_pointer
  logical :: saw(6)
  saw = .false.
  nullify(outer_pointer)
  call host(1, outer_pointer, saw)
  if (.not. all(saw)) then
    write(*,'(a)') 'host instance distinction failed'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED HOST INSTANCE OK'
end program i169c_associated_host_instance
