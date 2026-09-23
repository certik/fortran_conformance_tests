program main
  implicit none
  integer, dimension(2) :: a, b(3)
  a = [11,13]
  b = [17,19,23]
  call check_array(a, [11,13])
  call check_array(b, [17,19,23])
  print '(a)', 'type_declaration s002 array override ok'
contains
  subroutine check_array(value, expected)
    integer, intent(in) :: value(:), expected(:)
    if (size(value) /= size(expected)) error stop
    if (any(value /= expected)) error stop
  end subroutine check_array
end program main
