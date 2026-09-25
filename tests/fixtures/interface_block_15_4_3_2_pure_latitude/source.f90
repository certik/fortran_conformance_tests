program interface_block_pure_latitude
  implicit none
  integer :: observed
  ! rule: S15.4.3.2-014
  ! covers: interface omits PURE for a pure external function definition
  interface
    integer function pure_inc(i)
      integer, intent(in) :: i
    end function pure_inc
  end interface
  observed = -90
  observed = pure_inc(9)
  if (observed /= 10) error stop 1
  print '(a)', 'INTERFACE BLOCK PURE LATITUDE OK'
end program interface_block_pure_latitude

pure integer function pure_inc(i)
  implicit none
  integer, intent(in) :: i
  pure_inc = i + 1
end function pure_inc

pure integer function pure_inc_bad(i)
  implicit none
  integer, intent(in) :: i
  pure_inc_bad = i
end function pure_inc_bad
