! rule: S7.4.4.1-001
! covers: zero-and-positive-lengths
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(0) :: empty
character(1) :: one
character(4) :: four, words(2)
empty = ''
one = 'A'
four = 'abcd'
words = ['wxyz', 'QRST']
if (len(empty) /= 0 .or. empty%len /= 0) error stop 1
if (len(one) /= 1 .or. one%len /= 1) error stop 2
if (len(four) /= 4 .or. four%len /= 4) error stop 3
if (len(words) /= 4 .or. words%len /= 4) error stop 4
if (one /= 'A' .or. four /= 'abcd') error stop 5
if (words(1) /= 'wxyz' .or. words(2) /= 'QRST') error stop 6
end program
