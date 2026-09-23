program specification_expression_c1011_inquiries
  implicit none
  call observe([1,2,3,4,5,6,7], 'abcde', 7, 5)
  call observe([1,2,3,4], 'xyz', 4, 3)
  write(*,'(a)') 'SPECEXPR C1011 INQUIRIES OK'
contains
  subroutine observe(vals, word, expected_count, expected_len)
    integer, intent(in) :: vals(:), expected_count, expected_len
    character(len=*), intent(in) :: word
    integer :: a(size(vals,1))
    character(len=len(word)) :: copy
    if (size(a) /= expected_count) error stop 'SEC1011:size-inquiry'
    if (len(copy) /= expected_len) error stop 'SEC1011:len-inquiry'
  end subroutine observe
end program specification_expression_c1011_inquiries
