! rule: S10.2.1.3-021
! covers: representable-characters both-directions array-elements conversion-with-length-adjustment
! profile: iso10646
! F2023 10.2.1.3 p12. Only representable ASCII characters; padding is to default character.
program s10_2_1_3_021_valid
    implicit none
    integer, parameter :: unicode = selected_char_kind('ISO_10646')
    character(kind=unicode, len=3) :: wide
    character(kind=unicode, len=2) :: wide_array(2)
    character(3) :: narrow
    character(5) :: padded
    character(2) :: narrow_array(2)
    wide = achar(65, kind=unicode) // achar(122, kind=unicode) // achar(57, kind=unicode)
    narrow = wide
    if (narrow /= 'Az9') error stop 'unicode-to-default'
    narrow = 'By8'
    wide = narrow
    if (iachar(wide(1:1)) /= 66 .or. iachar(wide(2:2)) /= 121) error stop 'default-to-unicode'
    if (iachar(wide(3:3)) /= 56) error stop 'default-to-unicode-last'
    padded = wide
    if (padded /= 'By8  ') error stop 'conversion-with-length-adjustment'
    narrow_array = ['ab', 'CD']
    wide_array = narrow_array
    if (iachar(wide_array(1)(1:1)) /= 97) error stop 'array-to-unicode'
    if (iachar(wide_array(2)(2:2)) /= 68) error stop 'array-to-unicode-last'
    narrow_array = '??'
    narrow_array = wide_array
    if (any(narrow_array /= ['ab', 'CD'])) error stop 'array-to-default'
end program
