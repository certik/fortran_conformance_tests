program specification_expression_c1011_constant_inquiry
  implicit none
  integer, parameter :: fixed(7)=[1,2,3,4,5,6,7]
  integer :: a(size(fixed))
  if (size(a) /= 7) error stop 'SEC1011:constant-inquiry'
  write(*,'(a)') 'SPECEXPR C1011 CONSTANT INQUIRY OK'
end program specification_expression_c1011_constant_inquiry
