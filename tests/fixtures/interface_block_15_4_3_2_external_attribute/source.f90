program interface_block_external_attribute
  implicit none
  ! rule: S15.4.3.2-009
  ! covers: interface body supplies the EXTERNAL attribute without an EXTERNAL statement
  interface
    subroutine ext_marker(x)
      integer, intent(out) :: x
    end subroutine ext_marker
  end interface
  integer :: observed
  observed = -3
  call ext_marker(observed)
  if (observed /= 17) error stop 1
  print '(a)', 'INTERFACE BLOCK EXTERNAL ATTRIBUTE OK'
end program interface_block_external_attribute

subroutine ext_marker(x)
  implicit none
  integer, intent(out) :: x
  x = 17
end subroutine ext_marker

subroutine ext_marker_bad(x)
  implicit none
  integer, intent(out) :: x
  x = 16
end subroutine ext_marker_bad
