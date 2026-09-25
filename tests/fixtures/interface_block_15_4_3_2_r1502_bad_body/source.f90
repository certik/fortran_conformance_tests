program interface_block_body_control
  implicit none
  integer :: observed
  interface
    integer :: x
  end interface
  observed = -99
  observed = ext_body(36)
  if (observed /= 37) error stop 1
  print '(a)', 'INTERFACE BLOCK BODY CONTROL OK'
end program interface_block_body_control
integer function ext_body(i)
  implicit none
  integer, intent(in) :: i
  ext_body = i + 1
end function ext_body
