program interface_block_explicit_specific
  implicit none
  ! rule: S15.4.3.2-009
  ! covers: interface body supplies an explicit specific interface with an assumed-shape dummy
  interface
    integer function ext_vector_sum(values)
      integer, intent(in) :: values(:)
    end function ext_vector_sum
  end interface
  integer :: observed
  observed = -4
  observed = ext_vector_sum([11, 31])
  if (observed /= 42) error stop 1
  print '(a)', 'INTERFACE BLOCK EXPLICIT SPECIFIC OK'
end program interface_block_explicit_specific

integer function ext_vector_sum(values)
  implicit none
  integer, intent(in) :: values(:)
  ext_vector_sum = sum(values)
end function ext_vector_sum

integer function ext_vector_sum_bad(values)
  implicit none
  integer, intent(in) :: values(:)
  ext_vector_sum_bad = sum(values) - 1
end function ext_vector_sum_bad
