! rule: C1101
! covers: vector-subscript-selector-definition-rejected
program ab_c1101_vector
  implicit none
  integer :: store(4), idx(2)
  store=[1,2,3,4]; idx=[1,3]
  associate (a => store(idx))
    a=[9,8]
  end associate
end program ab_c1101_vector
