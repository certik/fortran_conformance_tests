program specification_expression_c1011_subscripts_typeparams
  implicit none
  call observe(2, 'abzz', 4)
  call observe(3, 'abczz', 7)
  write(*,'(a)') 'SPECEXPR C1011 SUBSCRIPTS TYPEPARAMS OK'
contains
  subroutine observe(n, text, expected_size)
    integer, intent(in) :: n, expected_size
    character(len=*), intent(in) :: text
    integer, parameter :: table(4)=[2,4,7,9]
    character(len=n) :: word
    integer :: a(table(n-1)+len(text(1:n)))
    if (len(word) /= n) error stop 'SEC1011:type-param'
    if (size(a) /= expected_size) error stop 'SEC1011:subscript-substring'
  end subroutine observe
end program specification_expression_c1011_subscripts_typeparams
