! rule: S6.3.2.2-005
! covers: select-type
! evidence: positive-control
program select_type_spellings
  implicit none
  call check(7)
contains
  subroutine check(value)
    class(*), intent(in) :: value
    selecttype(value)
    type is(integer)
      if (value /= 7) stop 1
    class default
      stop 2
    end select
    select type(value)
    type is(integer)
      if (value /= 7) stop 3
    class default
      stop 4
    end select
  end subroutine
end program
