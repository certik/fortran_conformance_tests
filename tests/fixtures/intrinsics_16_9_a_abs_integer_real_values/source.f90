! rule: S16.9.2-003
! covers: abs-integer-negative-to-positive
! covers: abs-integer-nonnegative-unchanged
! covers: abs-real-exact-sign-removal
! Oracles are exact inquiries, exact character/integer/small-real values, or source-stated ranges.
program intrinsics_16_9_a_abs_integer_real_values
  implicit none
  integer :: checks
  integer :: neg_i, pos_i
  real :: neg_r, pos_r
  checks=0
  neg_i = -7
  pos_i = 5
  neg_r = -2.0
  pos_r = 3.0
  neg_i = abs(neg_i)
  if (neg_i /= 7) then
    write(*,'(a)') 'I16A:abs_integer_real_values:integer-negative'
    error stop
  end if
  checks=checks+1
  pos_i = abs(pos_i)
  if (pos_i /= 5) then
    write(*,'(a)') 'I16A:abs_integer_real_values:integer-positive'
    error stop
  end if
  checks=checks+1
  neg_r = abs(neg_r)
  if (neg_r /= 2.0) then
    write(*,'(a)') 'I16A:abs_integer_real_values:real-negative'
    error stop
  end if
  checks=checks+1
  pos_r = abs(pos_r)
  if (pos_r /= 3.0) then
    write(*,'(a)') 'I16A:abs_integer_real_values:real-positive'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'I16A:abs_integer_real_values:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSICS 16.9 A ABS INTEGER REAL VALUES OK'
end program intrinsics_16_9_a_abs_integer_real_values
