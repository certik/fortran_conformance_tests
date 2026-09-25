program interface_block_abstract_pointer
  implicit none
  ! rule: S15.4.3.2-004
  ! covers: ABSTRACT INTERFACE used as a procedure pointer interface
  abstract interface
    subroutine action(x)
      integer, intent(out) :: x
    end subroutine action
  end interface
  procedure(action), pointer :: pp
  integer :: observed
  observed = -77
  pp => set_good
  call pp(observed)
  if (observed /= 33) error stop 1
  print '(a)', 'INTERFACE BLOCK ABSTRACT POINTER OK'
contains
  subroutine set_good(x)
    integer, intent(out) :: x
    x = 33
  end subroutine set_good
  subroutine set_bad(x)
    integer, intent(out) :: x
    x = 32
  end subroutine set_bad
end program interface_block_abstract_pointer
